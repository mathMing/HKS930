#!/usr/bin/env python3
"""Audit local mirror-test coverage against a contest task's requirements.

This is an honest coverage report, not an official ARC-Bench score. The test
files are matched by their leading requirement ID (for example REQ-1-1-1).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent
SPEC_ID = re.compile(r"^(REQ-[\d.-]+)\.spec\.(?:ts|js)$")


def load_atomic_ids(requirements: Path) -> list[str]:
    """Return atomic requirement IDs from the same YAML tree used by the agent."""
    return [str(node["id"]) for node in flatten(yaml.safe_load(requirements.read_text(encoding="utf-8")))]


def flatten(tree: dict) -> list[dict]:
    nodes: list[dict] = []

    def visit(node: dict) -> None:
        if str(node.get("type", "")).upper() == "ATOMIC":
            nodes.append(node)
        for child in node.get("children") or []:
            visit(child)

    visit(tree)
    return nodes


def audit(requirements: Path, tests_dir: Path) -> dict:
    raw_text = requirements.read_text(encoding="utf-8")
    tree = yaml.safe_load(raw_text)
    nodes = flatten(tree)
    mapped: dict[str, list[str]] = {str(node["id"]): [] for node in nodes}
    declarations: dict[str, list[str]] = {node_id: [] for node_id in mapped}
    for spec in sorted(tests_dir.glob("*.spec.*")):
        match = SPEC_ID.match(spec.name)
        if not match or match.group(1) not in mapped:
            continue
        mapped[match.group(1)].append(spec.name)
        try:
            source = spec.read_text(encoding="utf-8")
            titles = re.findall(r"\btest\s*\(\s*(['\"])(.*?)\1", source, re.DOTALL)
            declarations[match.group(1)].extend(title for _, title in titles)
        except OSError:
            pass
    mapped = {
        node_id: files if declarations[node_id] else []
        for node_id, files in mapped.items()
    }
    uncovered = [node_id for node_id, specs in mapped.items() if not specs]
    placeholder_scenarios = []
    placeholder_occurrences = 0
    dependency_errors = []
    details = {}
    node_ids = set(mapped)
    for node in nodes:
        description = " ".join(str(node.get("description", "")).split())
        details[str(node["id"])] = {
            "name": node.get("name", ""),
            "description": description,
            "dependencies": list(map(str, node.get("dependencies") or [])),
            "scenario_count": len(node.get("scenarios") or []),
            "description_usable": len(description) >= 80,
            "manual_review_required": True,
        }
        for dep in node.get("dependencies") or []:
            if str(dep) not in node_ids:
                dependency_errors.append({"requirement": node["id"], "missing_dependency": str(dep)})
        for scenario in node.get("scenarios") or []:
            content = " ".join(str(step.get("content", "")) for step in scenario.get("steps") or [])
            count = content.lower().count("the requested workflow")
            if count:
                placeholder_occurrences += count
                placeholder_scenarios.append({"requirement": node["id"], "scenario": scenario.get("name", ""),
                                              "placeholder_occurrences": count})
    return {
        "requirements": str(requirements),
        "tests_dir": str(tests_dir),
        "atomic_count": len(nodes),
        "covered_count": len(mapped) - len(uncovered),
        "uncovered": uncovered,
        "mapping": mapped,
        "test_titles": declarations,
        "requirement_details": details,
        "coverage_percent": round(100 * (len(mapped) - len(uncovered)) / len(mapped), 2) if mapped else 0,
        "degraded_scenarios": placeholder_scenarios,
        "placeholder_occurrences": raw_text.lower().count("the requested workflow"),
        "placeholder_occurrences_in_atomic_scenarios": placeholder_occurrences,
        "dependency_errors": dependency_errors,
        "spec_count": sum(len(specs) for specs in mapped.values()),
        "executed_count": None,
        "passed_count": None,
    }


def preflight(task: str, root: Path = ROOT) -> dict:
    """Validate that every hackathon atomic requirement has a mapped spec."""
    if task not in ("hackathon--github", "hackathon--sheet"):
        raise ValueError(f"unsupported task: {task}")
    requirements = root.parent / "arcbench-hackathon-requirements" / task / "requirements.yaml"
    tests_dir = root / "public-tests" / task
    if not requirements.is_file():
        raise FileNotFoundError(f"requirements file not found: {requirements}")
    if not tests_dir.is_dir():
        raise FileNotFoundError(f"Playwright test directory not found: {tests_dir}")
    result = audit(requirements, tests_dir)
    files = sorted(tests_dir.glob("*.spec.ts"))
    result["unknown_spec_files"] = [p.name for p in files
                                    if not (m := SPEC_ID.match(p.name)) or m.group(1) not in result["mapping"]]
    return result


def write_report(result: dict, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    task = Path(result["requirements"]).parent.name
    json_path = output_dir / f"{task}-audit.json"
    md_path = output_dir / f"{task}-audit.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [f"# {task} requirement audit", "", "This is a local audit, not an official score.", "",
             f"- Atomic requirements: {result['atomic_count']}",
             f"- Requirements with specs: {result['covered_count']}",
             f"- Spec files mapped: {result['spec_count']}",
             f"- Placeholder scenario occurrences: {result['placeholder_occurrences']}",
             f"- Placeholder occurrences inside atomic scenario steps: {result['placeholder_occurrences_in_atomic_scenarios']}",
             f"- Missing dependency references: {len(result['dependency_errors'])}", "", "## Requirement coverage", "",
             "| ID | Name | Dependencies | Specs | Test title(s) | Description / review note |", "|---|---|---|---:|---|---|"]
    tree = yaml.safe_load(Path(result["requirements"]).read_text(encoding="utf-8"))
    for node in flatten(tree):
        nid = str(node["id"])
        placeholder = any(row["requirement"] == nid for row in result["degraded_scenarios"])
        deps = ", ".join(map(str, node.get("dependencies") or [])) or "—"
        tests = "<br>".join(result.get("test_titles", {}).get(nid, []))
        detail = result["requirement_details"][nid]
        description = detail["description"][:240].replace("|", "\\|")
        review = "scenario text damaged; use description; manual review required" if placeholder else "description testable; manual review required"
        lines.append(f"| {nid} | {node.get('name', '')} | {deps} | {len(result['mapping'][nid])} | {tests} | {description}<br><em>{review}</em> |")
    if result["dependency_errors"]:
        lines.extend(["", "## Missing dependency references", ""])
        lines.extend(f"- {x['requirement']} references missing {x['missing_dependency']}" for x in result["dependency_errors"])
    if result["degraded_scenarios"]:
        lines.extend(["", "## Damaged scenarios (source YAML left unchanged)", ""])
        lines.extend(f"- {x['requirement']} / {x['scenario']}: {x['placeholder_occurrences']} placeholder occurrence(s)"
                     for x in result["degraded_scenarios"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=("hackathon--github", "hackathon--sheet"))
    parser.add_argument("--requirements", type=Path)
    parser.add_argument("--tests", type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--require-full", action="store_true", help="fail if any atomic requirement lacks a spec")
    parser.add_argument("--preflight", action="store_true", help="check spec coverage before a model run")
    parser.add_argument("--write-report", action="store_true", help="write JSON and Markdown audit under arc/audits")
    args = parser.parse_args(argv)
    req = args.requirements or ROOT.parent / "arcbench-hackathon-requirements" / args.task / "requirements.yaml"
    tests = args.tests or ROOT / "public-tests" / args.task
    if not req.is_file():
        parser.error(f"requirements file not found: {req}")
    result = audit(req, tests)
    if args.preflight:
        result = preflight(args.task)
    if args.write_report:
        for path in write_report(result, ROOT / "audits"):
            print(f"Wrote {path}")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{args.task} 本地需求镜像覆盖：{result['covered_count']}/{result['atomic_count']} "
              f"({result['coverage_percent']}%)")
        print("这不是官方比赛分数。")
        if result["uncovered"]:
            print("尚无测试的需求：" + ", ".join(result["uncovered"]))
        if result["degraded_scenarios"]:
            print(f"需求文件全文有 {result['placeholder_occurrences']} 处占位短语；其中原子场景步骤有 "
                  f"{result['placeholder_occurrences_in_atomic_scenarios']} 处、涉及 "
                  f"{len(result['degraded_scenarios'])} 条场景，需人工核对。")
    return 1 if (args.require_full or args.preflight) and (result["uncovered"] or result.get("unknown_spec_files")) else 0


if __name__ == "__main__":
    sys.exit(main())
