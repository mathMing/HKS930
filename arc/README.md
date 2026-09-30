# arc/ — 在这一个仓库里完成 ARC-Bench 的改、测、交

这个目录是 Octos 参加 ARC-Bench 的全部外围：平台适配包、公开验收测试、本地做题和打分脚本。
学员只需要这一个仓库。内核源码在上一级（`crates/`），适配包在这里。

## 五步

```sh
# 0. 准备（一次）
pip install -r arc/requirements.txt          # pyyaml、arcbench-runtime
export ARCBENCH_API_KEY=ak_...               # arc-bench.com 个人页的 API key
export NODE_BIN=/opt/homebrew/opt/node@24/bin # 你的 node 目录（Linux 一般不用设）

# 1. 拿一个 Octos 二进制：官方版，或自己编的魔改版
export OCTOS_BIN=/path/to/octos              # 不设则依次找 bin/octos、PATH、../target/release/octos，最后从 release 下载
cargo build --release -p octos-cli --no-default-features --features api   # 编魔改版时

# 2. 本机做题（约 5 分钟，不到一分钱）
python3 arc/run-task-local.py arc/tasks/smoke--counter --name try1
#    --port 43300 换端口可并行跑多题；--template <已有产物目录> 进入 evolution 模式
#    （先跑 smoke--counter，再以它的产物为模板跑 smoke-evolution--counter）

# 3. 用平台原版 Playwright 测试打分（首次会自动装 Playwright）
python3 arc/grade-local.py arc/arc-output/try1 smoke--counter
python3 arc/metrics.py arc/arc-output/try1        # 轮数 / Token / 费用 / 耗时 / 节点状态 / 打分，一行表格
python3 -m unittest discover -s arc/tests -t arc  # 编排器纯函数的单元测试

# 4. 改一处：main.py 的提示词 / 环境变量，octos_stdio.py 的启动参数，或 crates/ 里的内核
#    改完回到第 2、3 步，改前改后各跑一次，比数字

# 5. 打包上传
sh arc/pack.sh                               # 得到 octos-arc-bundle.zip
# 到 arc-bench.com 对应比赛页 New submission 上传，模型填 deepseek-v4-flash，
# Base URL 填 https://api.arc-bench.com/v1，然后选题、Run
```

## 改了内核怎么让平台用上

平台运行时按 `main.py` 里 `OCTOS_RELEASE_URL` 现场下载 Octos。改了 `crates/` 之后必须：
编译 Linux x86_64 版 → 在本仓库发一个 Release 挂上 tar.gz → 把 `OCTOS_RELEASE_URL` 改成那个地址 → 重新 `pack.sh` 上传。
否则平台跑的仍是官方版，改了等于没改。

## 目录

| 文件 | 作用 |
|---|---|
| `main.py` | 平台入口（胶水）：读平台环境、按需求树生成本题的 pipeline（`.dot`）、起内核并点名运行、收集产物与 7 张表 |
| `verify_node.py` | 验收节点跑的命令：构建、起服务、跑该节点的公开 Playwright spec；失败时打印报错和出错时的页面快照；按次数和截止时间决定是否停止修复（打印 `ARC_NO_MORE_REPAIRS`）；`--seed` 模式把现有应用铺进运行目录 |
| `octos_stdio.py` | 通过 `octos serve --stdio` 驱动内核 |
| `arc-policy.toml` | 全部可调参数（`[pipeline]` 段），每项都有 `OCTOS_*` 环境变量覆盖 |
| `prompts/pipeline-implement.md` / `pipeline-regression.md` / `port-contract.md` | 实现节点、全量回归修复节点、双端口约定的提示词 |
| `public-tests/<题目>/` | 平台公开的 Playwright 验收测试 |
| `tasks/<题目>/` | 各题需求文件的离线副本 |
| `template/` | 平台初始工作区模板：pack.sh 打进 zip 根 |
| `run-task-local.py` / `grade-local.py` / `pack.sh` | 本机做题、按平台口径打分（单测 10 秒超时）、打包 |

## 流程（内核的 DAG 调度器执行，胶水不做编排）

```
start -> impl_<需求1> -> check_<需求1> -> impl_<需求2> -> ... -> check_all -> done
                    ^______________|  (失败回边 = 修复轮)            |      ^
                                                          fix_all <-+------+
```

- 一个需求怎么修都不过时，打印停止标记，继续做下一个需求，不会把后面的需求全部跳过。
- 修复轮数受 `repair_rounds` 和截止时间双重限制；截止时间给后面每个需求留出最少时间。
- 最后跑一遍全部公开测试，坏了的再修（`final_repair_rounds` 轮）。
- 整体预算 = max(`run_timeout_seconds`, `node_budget_seconds` × 需求数)。

## 常用开关

| 变量 | 默认 | 作用 |
|---|---|---|
| `OCTOS_REPAIR_ROUNDS` | 5 | 每个需求最多修几轮 |
| `OCTOS_ARC_FINAL_REPAIRS` | 2 | 全量回归后最多修几轮 |
| `OCTOS_TIME_BUDGET` / `OCTOS_NODE_TIME_BUDGET` | 3600 / 600 | 整体预算下限 / 每个需求的预算 |
| `OCTOS_NODE_TIMEOUT` | 1200 | 单个实现节点的时限 |
| `OCTOS_ARC_REASONING` | none | 每个模型调用的思考强度（none/low/medium/high/max） |
| `OCTOS_ARC_NODE_MAX_TOKENS` | 32768 | 单次调用输出上限 |
| `OCTOS_ARC_LLM_TIMEOUT` | 900 | 单次（非流式）模型请求的时限 |
| `OCTOS_ARC_CONTEXT_WINDOW` | 0 | 端点实际上下文比模型标称小时设它（例如本地 32768） |

## Hackathon GitHub / Spreadsheet 离线准备

两个任务的需求数据位于仓库根目录 `arcbench-hackathon-requirements/`。没有 ARC API Key 时仍可先做需求审计、编写 Playwright 镜像测试和检查打包结构：

```sh
python arc/github_eval.py hackathon--github --write-report
python arc/github_eval.py hackathon--sheet --write-report
python arc/run-task-local.py --check hackathon--github
python arc/run-task-local.py --check hackathon--sheet
```

镜像测试放在 `arc/public-tests/hackathon--github/` 和 `arc/public-tests/hackathon--sheet/`，文件名用需求 ID 开头。评分时传赛道名而非需求 ID，例如 `python arc/grade-local.py <应用产物目录> hackathon--github`。该评分器会复制应用到临时目录；测试数据不会写入原产物。记录的镜像分是本地对照指标，不是 ARC-Bench 官方成绩。

逐项映射和未执行/待人工核对事项见 `arc/audits/hackathon--github-audit.md`、`hackathon--sheet-audit.md` 和 `manual-review-notes.md`。Spec 数只代表已经编写并映射的用例；当前还没有对生成应用执行，因此不是通过数。

两任务全流程按赛事顺序 GitHub → Spreadsheet 运行：

```sh
python arc/contest-local.py --check  # 离线确认两份需求都可读取
python arc/contest-local.py          # 需要 Octos、模型 API 配置与可用额度
```

本地双任务驱动会先检查每项的 `.arc/run-summary.json` 中
`pipeline_completed` 是否为 true；若 Octos 只生成了部分应用就中断，
不会把这份残缺应用当作完整基线评分，也不会继续消耗下一赛道预算。
验收卡住时可查看 Octos 临时运行目录中的 `.arc-verify-progress.json`：
它只记录当前阶段、时间与进程号，不含密钥；独立运行验收成功返回功能失败
也说明浏览器链路正常，须和基础设施超时区别对待。

第三版把每次验收的结果写到交付目录 `.arc/check-results.jsonl`，并在主日志
输出 `[arc-check]` 摘要：需求 ID、尝试次数、阶段、退出码、失败类别及脱敏报错。
`application_failure` 仍可修复；确定的 `infrastructure_failure` 会停止整轮，
`.arc/run-summary.json` 标记为不可评分且记录故障节点与原因。此时仅保留已验证
快照，不用未验收的半成品覆盖交付目录；本地双任务驱动不会评分或开始下一任务。

Spreadsheet 需求文件包含损坏/占位场景。审计报告会将其单独列出；不要把占位场景改写成验收断言，测试应依据该原子需求自身的功能描述。

打包脚本默认拒绝覆盖已有 `octos-arc-bundle.zip`。需要验证或另存时，可设置 `OUTPUT_ZIP` 为一个新的输出路径；脚本只清理暂存目录，不改工作树源文件。
| `OCTOS_ARC_TEST_TIMEOUT_MS` | 10000 | 本地验收单测超时（与平台一致） |
