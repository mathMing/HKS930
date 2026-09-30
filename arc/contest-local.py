#!/usr/bin/env python3
"""Run the two hackathon tasks in the required order, then print local metrics.

Each task starts from its own clean generic skeleton and receives a distinct
output directory. A failure stops the sequence to avoid scoring a partial run
as a completed two-task entry.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = ("hackathon--github", "hackathon--sheet")


def completed_pipeline(output: Path) -> bool:
    """An adapter exit code alone does not mean Octos finished its pipeline."""
    report = output / ".arc" / "run-summary.json"
    try:
        return json.loads(report.read_text(encoding="utf-8")).get("pipeline_completed") is True
    except (OSError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate task files without calling the model")
    parser.add_argument("--name", help="optional run label; unique per-task suffixes are appended")
    parser.add_argument("--port", type=int, default=43100)
    args = parser.parse_args()
    requirements = ROOT.parent / "arcbench-hackathon-requirements"
    for task in TASKS:
        path = requirements / task / "requirements.yaml"
        if not path.is_file():
            parser.error(f"missing task requirements: {path}")
    if args.check:
        for task in TASKS:
            checked = subprocess.run([sys.executable, str(ROOT / "github_eval.py"), task, "--preflight"],
                                     cwd=ROOT, check=False)
            if checked.returncode:
                print(f"Preflight failed for {task}; no model run was started.")
                return checked.returncode
        print("Both tasks fully mapped and available in required order: " + " -> ".join(TASKS))
        return 0
    run_id = args.name or uuid.uuid4().hex[:8]
    for index, task in enumerate(TASKS):
        name = f"{run_id}-{task}"
        port = args.port + index * 2
        command = [sys.executable, str(ROOT / "run-task-local.py"), task,
                   "--name", name, "--port", str(port)]
        print(f"\n=== Starting {index + 1}/2: {task} ===", flush=True)
        result = subprocess.run(command, cwd=ROOT.parent)
        if result.returncode:
            print(f"Stopped: {task} returned {result.returncode}; Spreadsheet was not started.")
            return result.returncode
        output = ROOT / "arc-output" / name
        if not completed_pipeline(output):
            try:
                report = json.loads((output / ".arc" / "run-summary.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                report = {}
            reason = (f"infrastructure failure at {report.get('failure_node')}: {report.get('failure_reason')}"
                      if report.get("status") == "infrastructure_failure" else "pipeline did not finish")
            print(f"Stopped: {task} {reason}; partial app was not graded and next task was not started.")
            return 7
        grade = subprocess.run([sys.executable, str(ROOT / "grade-local.py"), str(output), task,
                                str(port)], cwd=ROOT.parent)
        if grade.returncode:
            print(f"Stopped: local mirror grading failed for {task}; next task was not started.")
            return grade.returncode
        metrics = subprocess.run([sys.executable, str(ROOT / "metrics.py"), str(output), "--json"],
                                 cwd=ROOT.parent, capture_output=True, text=True)
        if metrics.returncode == 0:
            parsed = json.loads(metrics.stdout)
            print(f"Run metrics: duration={parsed.get('duration_s')}s, cost={parsed.get('cost')}, "
                  f"local_mirror={parsed.get('grade')}")
    print("Both tasks completed in order. Local mirror results are not official competition scores.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
