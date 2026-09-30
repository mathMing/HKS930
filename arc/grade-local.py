#!/usr/bin/env python3
"""Run a local Playwright suite against a disposable copy of a generated app.

Usage: grade-local.py <output_dir> <task_id> [port]

For the hackathon task IDs, the JSON result is explicitly a local requirement
mirror, not an official ARC-Bench score.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path


CONTEST_TASKS = {"hackathon--github", "hackathon--sheet"}
APP_INSTALL = "npm install --no-audit --no-fund --no-package-lock"


def configure_text_streams() -> None:
    """Avoid crashing while printing Unicode Playwright reporter output."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                continue


def app_install_steps(app: Path) -> list[tuple[Path, str]]:
    """Return build/install commands to run only inside the disposable app copy."""
    return [(app / "frontend", f"{APP_INSTALL} && npm run build"),
            (app / "backend", APP_INSTALL)]


def port_is_free(port: int) -> bool:
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) != 0


def stop_server(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        if os.name != "nt":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True, check=False, timeout=10)
        proc.wait(timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        try:
            proc.kill()
            proc.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass


def walk_report(suites):
    for suite in suites or []:
        for spec in suite.get("specs", []):
            tests = spec.get("tests", [])
            yield spec.get("title", "(untitled)"), bool(tests) and all(
                test.get("status") == "expected" or test.get("ok") for test in tests)
        yield from walk_report(suite.get("suites", []))


def save_infrastructure_failure(out: Path, task_id: str, reason: str) -> None:
    arc = out / ".arc"
    arc.mkdir(exist_ok=True)
    target = arc / f"{task_id}-local-grade.json"
    target.write_text(json.dumps({
        "task": task_id,
        "score_type": "local_requirement_mirror_not_official" if task_id in CONTEST_TASKS else "local_public_test",
        "status": "infrastructure_failure",
        "requirements_total": None,
        "requirements_mapped": None,
        "spec_files_mapped": None,
        "passed": None,
        "total": None,
        "executed": 0,
        "failed": None,
        "elapsed_seconds": None,
        "infrastructure_error": reason,
        "tests": [],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def install_playwright(grader: Path, env: dict[str, str]) -> tuple[bool, str]:
    cli = grader / "node_modules" / "@playwright" / "test" / "cli.js"
    if cli.is_file():
        return True, ""
    grader.mkdir(parents=True, exist_ok=True)
    manifest = grader / "package.json"
    if not manifest.exists():
        manifest.write_text('{"name":"arc-local-grader","private":true}\n', encoding="utf-8")
    cmd = "npm install --no-audit --no-fund @playwright/test && npx playwright install chromium"
    try:
        result = subprocess.run(cmd, cwd=grader, env=env, shell=True, capture_output=True, text=True,
                                encoding="utf-8", errors="replace",
                                timeout=int(os.environ.get("ARC_GRADE_INSTALL_TIMEOUT_SECONDS", "600")))
    except subprocess.TimeoutExpired as exc:
        details = (exc.stdout or b"") + (exc.stderr or b"")
        if isinstance(details, bytes):
            details = details.decode(errors="replace")
        return False, f"Playwright installation timed out\n{details[-2000:]}"
    if result.returncode or not cli.is_file():
        return False, (result.stdout + result.stderr)[-3000:]
    return True, ""


def grade_suite(out: Path, task_id: str, port: int, root: Path, specs: Path) -> int:
    if not out.is_dir():
        print(f"[grade] application output does not exist: {out}")
        return 2
    if not specs.is_dir() or not list(specs.glob("*.spec.ts")):
        reason = f"no Playwright specs found at {specs}"
        save_infrastructure_failure(out, task_id, reason)
        print(f"[grade] {task_id}:不可评分：{reason}")
        return 4
    if not port_is_free(port):
        save_infrastructure_failure(out, task_id, f"port {port} is already serving")
        print(f"[grade] port {port} is already serving; refusing to score another process")
        return 5

    grader = root / "local-grader"
    env = os.environ.copy()
    node_dir = os.environ.get("NODE_BIN") or (str(Path(shutil.which("node")).parent) if shutil.which("node") else "")
    if node_dir and Path(node_dir).is_dir():
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
    ok, install_log = install_playwright(grader, env)
    if not ok:
        save_infrastructure_failure(out, task_id, f"Playwright setup failed: {install_log[-1500:]}")
        print(f"[grade] Playwright setup failed; result is not scorable:\n{install_log}")
        return 6

    for part in ("frontend", "backend"):
        if not (out / part).is_dir():
            reason = f"missing required app directory: {out / part}"
            save_infrastructure_failure(out, task_id, reason)
            print(f"[grade] infrastructure failure: {reason}")
            return 2

    node = shutil.which("node", path=env.get("PATH"))
    cli = grader / "node_modules" / "@playwright" / "test" / "cli.js"
    temp_root = Path(tempfile.mkdtemp(prefix=f".run-{task_id}-", dir=grader))
    app = temp_root / "app"
    work = temp_root / "tests-run"
    server = None
    started = time.monotonic()
    result = None
    failure = None
    try:
        for part in ("frontend", "backend"):
            source = out / part
            shutil.copytree(source, app / part, ignore=shutil.ignore_patterns("node_modules", "dist"))

        for cwd, command in app_install_steps(app):
            try:
                built = subprocess.run(command, cwd=cwd, env=env, shell=True, capture_output=True,
                                       text=True, encoding="utf-8", errors="replace",
                                       timeout=int(os.environ.get("ARC_GRADE_BUILD_TIMEOUT_SECONDS", "600")))
            except subprocess.TimeoutExpired:
                failure = f"install/build timed out in {cwd.name}"
                break
            if built.returncode:
                failure = f"install/build failed in {cwd.name}: {(built.stdout + built.stderr)[-2000:]}"
                break
        if failure:
            save_infrastructure_failure(out, task_id, failure)
            print(f"[grade] infrastructure failure: {failure}")
            shutil.rmtree(temp_root, ignore_errors=True)
            return 6

        data_dir = temp_root / "test-data"
        data_dir.mkdir()
        server_env = dict(env, PORT=str(port), ARCBENCH_TEST_DATA_DIR=str(data_dir))
        start_command = "npm run start"
        server = subprocess.Popen(start_command, cwd=app / "backend", env=server_env, shell=True,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                                  preexec_fn=None if os.name == "nt" else os.setsid)
        for _ in range(60):
            if not port_is_free(port):
                break
            if server.poll() is not None:
                failure = f"application server exited with code {server.returncode}"
                break
            time.sleep(0.5)
        if failure or port_is_free(port):
            failure = failure or f"application server did not bind port {port} within 30 seconds"
            save_infrastructure_failure(out, task_id, failure)
            print(f"[grade] infrastructure failure: {failure}")
            shutil.rmtree(temp_root, ignore_errors=True)
            return 3

        shutil.copytree(specs, work / "tests", ignore=shutil.ignore_patterns("playwright.config.ts", ".gitkeep"))
        report = (work / "report.json").resolve()
        config = work / "playwright.config.ts"
        config.write_text(
            "import { defineConfig } from '@playwright/test';\n"
            "export default defineConfig({ testDir: './tests', timeout: %s, retries: 0, workers: 1, "
            "reporter: [['json', { outputFile: %s }], ['line']], "
            "use: { headless: true, baseURL: process.env.E2E_BASE_URL } });\n"
            % (os.environ.get("ARC_GRADE_TIMEOUT_MS", "10000"), json.dumps(str(report))), encoding="utf-8")
        test_env = dict(env, E2E_BASE_URL=f"http://127.0.0.1:{port}")
        result = subprocess.run([node or "node", str(cli), "test", "-c", str(config)], cwd=grader,
                                env=test_env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace",
                                timeout=int(os.environ.get("ARC_GRADE_RUN_TIMEOUT_SECONDS", "900")))
        if result.stdout:
            print(result.stdout[-4000:])
        if result.stderr:
            print(result.stderr[-2500:])
    except subprocess.TimeoutExpired:
        failure = "Playwright suite timed out"
    except OSError as exc:
        failure = f"could not start grading process: {exc}"
    finally:
        stop_server(server)

    output_arc = out / ".arc"
    output_arc.mkdir(exist_ok=True)
    report_path = work / "report.json"
    report_target = output_arc / f"{task_id}-playwright-report.json"
    report_data = None
    if report_path.is_file():
        try:
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
            shutil.copy2(report_path, report_target)
        except (OSError, json.JSONDecodeError) as exc:
            failure = f"invalid Playwright report: {exc}"
    else:
        failure = failure or "Playwright did not produce a JSON report"

    results = list(walk_report((report_data or {}).get("suites", [])))
    passed = sum(ok for _, ok in results)
    is_contest_task = task_id in CONTEST_TASKS
    requirement_count = mapped_count = spec_count = None
    if is_contest_task:
        try:
            sys.path.insert(0, str(root))
            import github_eval
            audit = github_eval.preflight(task_id, root)
            requirement_count = audit["atomic_count"]
            mapped_count = audit["covered_count"]
            spec_count = audit["spec_count"]
        except (OSError, ValueError, KeyError) as exc:
            failure = failure or f"requirement/spec audit failed: {exc}"
    status = "infrastructure_failure" if failure else ("completed" if passed == len(results) else "completed_with_test_failures")
    grade = {
        "task": task_id,
        "score_type": "local_requirement_mirror_not_official" if is_contest_task else "local_public_test",
        "status": status,
        "requirements_total": requirement_count,
        "requirements_mapped": mapped_count,
        "spec_files_mapped": spec_count,
        "passed": passed,
        "total": len(results),
        "executed": len(results),
        "failed": len(results) - passed,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "infrastructure_error": failure,
        "playwright_exit_code": result.returncode if result else None,
        "report": str(report_target) if report_target.is_file() else None,
        "tests": [{"title": title, "ok": ok} for title, ok in results],
    }
    grade_path = output_arc / f"{task_id}-local-grade.json"
    grade_path.write_text(json.dumps(grade, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.rmtree(temp_root, ignore_errors=True)

    if not results or failure:
        print(f"[grade] {task_id}: 不可评分；{failure or '测试报告中没有执行用例'}")
        return 6
    label = "本地需求镜像分（非官方成绩）" if is_contest_task else "本地公开测试"
    print(f"[grade] {label} {task_id}: requirements={mapped_count}/{requirement_count}; "
          f"tests={passed}/{len(results)}; elapsed={grade['elapsed_seconds']}s")
    for title, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {title}")
    return 0


def main(argv: list[str]) -> int:
    configure_text_streams()
    if len(argv) < 2:
        print(__doc__)
        return 2
    out = Path(argv[0]).resolve()
    task_id = argv[1]
    port = int(argv[2]) if len(argv) > 2 else 43300
    root = Path(__file__).resolve().parent
    if task_id in CONTEST_TASKS:
        task = root.parent / "arcbench-hackathon-requirements" / task_id
        if not (task / "requirements.yaml").is_file():
            print(f"[grade] missing task requirements: {task / 'requirements.yaml'}")
            return 2
    return grade_suite(out, task_id, port, root, root / "public-tests" / task_id)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
