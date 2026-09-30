import argparse
import json
import os
from pathlib import Path
import socket
import sys
import uuid
import shutil
import subprocess
from local_api_config import resolve_api_settings
from local_runtime import add_windows_shell_path


parser = argparse.ArgumentParser()
parser.add_argument("task", nargs="?"); parser.add_argument("--check", action="store_true"); parser.add_argument("--name", default=None)
parser.add_argument("--port", type=int, default=43100, help="grading port the app must serve (default 43100)")
parser.add_argument("--smoke-port", type=int, default=None, help="port for the agent's own smoke tests (default port+1)")
parser.add_argument("--template", default=None, help="existing generated app to evolve (copied into the output dir first)")
arguments = parser.parse_args()
root = Path(__file__).resolve().parent
adapter = root
_cands = [os.environ.get("OCTOS_BIN"),
          root.parent / "target" / "release" / "octos",
          root.parent / "target" / "release" / "octos.exe",
          root.parent / "target" / "debug" / "octos",
          root.parent / "target" / "debug" / "octos.exe",
          shutil.which("octos"), shutil.which("octos.exe")]
binary = next((Path(c).resolve() for c in _cands if c and Path(c).is_file()), None)
python = Path(sys.executable)
task_names = [arguments.task or "arc-counter-task"]
task_dirs = []
for name in task_names:
    if Path(name).exists():
        candidate = Path(name).resolve()
    elif name in ("hackathon--github", "hackathon--sheet"):
        candidate = root.parent / "arcbench-hackathon-requirements" / name
    else:
        candidate = Path(name).resolve()
    if not (candidate / "requirements.yaml").is_file():
        sys.exit(f"找不到任务需求文件：{candidate / 'requirements.yaml'}")
    task_dirs.append(candidate)
if arguments.check:
    for task in task_dirs:
        print(f"需求检查通过：{task / 'requirements.yaml'}")
        if task.name in ("hackathon--github", "hackathon--sheet"):
            audit = subprocess.run(
                [str(python), str(adapter / "github_eval.py"), task.name, "--preflight"],
                cwd=adapter, check=False)
            if audit.returncode:
                sys.exit(audit.returncode)
    sys.exit(0)
# An OpenAI key must never silently become an ARC platform credential: only
# accept it when the caller also pinned OPENAI_BASE_URL to their own endpoint,
# otherwise the key would be sent to api.arc-bench.com.
try:
    key, base_url = resolve_api_settings(dict(os.environ), root.parent / "api.txt")
except ValueError as exc:
    sys.exit(str(exc))
if not key:
    sys.exit("未找到可用 API Key：设置 ARCBENCH_API_KEY，或在本地 api.txt 配置 OpenAI 兼容 Key 和 Base URL。")
config = {"base_url": base_url, "model": os.environ.get("MODEL", "deepseek-v4-flash")}
for required in (python, adapter / "main.py"):
    if not required.is_file():
        sys.exit(f"缺少文件：{required}")
if not binary:
    sys.exit("找不到 octos 二进制：设 OCTOS_BIN，或先编译/放入 target/release/octos")
environment = os.environ.copy()
for name in ("OCTOS_HOME", "OCTOS_CONFIG_DIR", "ARCBENCH_TEMPLATE_DIR", "ARCBENCH_TASK_DIR", "OCTOS_INSTANCE_DATA_DIR", "OCTOS_DANGER_FULL_ACCESS"):
    environment.pop(name, None)
# The container mounts the public specs at /workspace/tests; locally they
# live in the repo. main.py reads this only as the local fallback.
def run_one(task: Path) -> int:
    environment = add_windows_shell_path(os.environ.copy())
    for name in ("OCTOS_HOME", "OCTOS_CONFIG_DIR", "ARCBENCH_TEMPLATE_DIR", "ARCBENCH_TASK_DIR", "OCTOS_INSTANCE_DATA_DIR", "OCTOS_DANGER_FULL_ACCESS"):
        environment.pop(name, None)
    # Start from the same empty web skeleton the platform supplies. This also
    # makes the pipeline's seed check idempotent on Windows, where the kernel
    # sandbox may not be able to copy into a newly created workspace directory.
    environment["ARCBENCH_TEMPLATE_DIR"] = str(root / "template")
    # `verify_node.py` otherwise searches the entire POSIX `/` tree for
    # Playwright. Under Windows + MSYS that can walk mounted drives for minutes.
    local_playwright = root / "local-grader"
    if (local_playwright / "node_modules" / "@playwright" / "test" / "cli.js").is_file():
        environment["OCTOS_ARC_PLAYWRIGHT_ROOT"] = str(local_playwright)
    local_tests = root / "public-tests" / task.name
    if local_tests.is_dir():
        environment["OCTOS_ARC_LOCAL_TESTS"] = str(local_tests)
    environment.update(
    OCTOS_BIN=str(binary),
    OPENAI_API_KEY=key,
    OPENAI_BASE_URL=config["base_url"],
    MODEL=config["model"],
    OCTOS_MODEL=config["model"],
    OCTOS_PROVIDER="custom",
    # No OCTOS_MAX_ITERATIONS / OCTOS_NODE_TIMEOUT / OCTOS_TIME_BUDGET here:
    # local practice must run under the same arc-policy.toml limits as the
    # real competition, otherwise practice scores are optimistic and tuning
    # targets the wrong conditions.
    OCTOS_SMOKE_PORT=str(arguments.smoke_port or arguments.port + 1),
    )
    node_dir = os.environ.get("NODE_BIN") or (str(Path(shutil.which("node")).parent) if shutil.which("node") else "")
    if node_dir and Path(node_dir).is_dir():
        environment["PATH"] = node_dir + os.pathsep + environment["PATH"]
    else:
        print("警告：未找到 node（按当前 PATH 继续）；需要时用 NODE_BIN 指定", flush=True)
    print(f"运行时：{binary}", flush=True)
    print(f"需求：{task / 'requirements.yaml'}", flush=True)
    print(f"模型：{config['model']}；密钥：已读取（不显示）", flush=True)
    if arguments.check:
        return 0
    port = arguments.port
    smoke_port = arguments.smoke_port or arguments.port + 1
    for selected_port in (port, smoke_port):
        with socket.socket() as listener:
            try:
                listener.bind(("127.0.0.1", selected_port))
            except OSError:
                print(f"端口 {selected_port} 已占用，未启动；不会终止已有服务。")
                return 1
    output = root / "arc-output" / (arguments.name or f"{task.name}-{uuid.uuid4().hex[:8]}")
    print(f"交付目录：{output}", flush=True)
    if arguments.template:
        template = Path(arguments.template).resolve()
        if not (template / "frontend").is_dir() or not (template / "backend").is_dir():
            print(f"模板目录缺少 frontend/ 或 backend/：{template}")
            return 1
        if output.exists():
            print(f"交付目录已存在，不覆盖：{output}")
            return 1
        shutil.copytree(template, output, symlinks=True,
                        ignore=shutil.ignore_patterns("node_modules", "dist", "requirements", "skill-output", ".octos",
                                                      "octos-events.jsonl", "runner-events.jsonl", "llm-usage.jsonl", "design"))
    command = [str(python), "main.py", str(task), "--output-dir", str(output), "--type", "web", "--web-port", str(port)]
    return subprocess.run(command, cwd=adapter, env=environment).returncode

task = task_dirs[0]
print(f"需求：{task / 'requirements.yaml'}", flush=True)
sys.exit(run_one(task))
