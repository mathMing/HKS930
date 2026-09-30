import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import github_eval


class RequirementAuditTests(unittest.TestCase):
    def test_maps_only_requirement_named_specs_and_finds_missing_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.yaml"
            requirements.write_text(
                """id: ROOT
type: FOLDER
children:
  - id: REQ-1-1
    type: ATOMIC
    name: first
    dependencies: []
    scenarios: []
  - id: REQ-1-2
    type: ATOMIC
    name: second
    dependencies: [REQ-MISSING]
    scenarios: []
""",
                encoding="utf-8",
            )
            specs = root / "specs"
            specs.mkdir()
            (specs / "REQ-1-1.spec.ts").write_text("test('mapped')", encoding="utf-8")
            (specs / "other.spec.ts").write_text("test('unmapped')", encoding="utf-8")

            report = github_eval.audit(requirements, specs)

        self.assertEqual(report["atomic_count"], 2)
        self.assertEqual(report["covered_count"], 1)
        self.assertEqual(report["uncovered"], ["REQ-1-2"])
        self.assertEqual(report["test_titles"]["REQ-1-1"], ["mapped"])
        self.assertEqual(report["dependency_errors"], [
            {"requirement": "REQ-1-2", "missing_dependency": "REQ-MISSING"}
        ])

    def test_preflight_accepts_complete_mapping_and_rejects_uncovered_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            req = root / "arcbench-hackathon-requirements" / "hackathon--github" / "requirements.yaml"
            req.parent.mkdir(parents=True)
            req.write_text("""id: ROOT
type: FOLDER
children:
  - {id: REQ-1, type: ATOMIC, name: first, description: feature}
  - {id: REQ-2, type: ATOMIC, name: second, description: feature}
""", encoding="utf-8")
            tests = root / "arc" / "public-tests" / "hackathon--github"
            tests.mkdir(parents=True)
            (tests / "REQ-1.spec.ts").write_text("test('REQ-1 visible flow', async () => {});", encoding="utf-8")

            incomplete = github_eval.preflight("hackathon--github", root / "arc")
            self.assertEqual(incomplete["uncovered"], ["REQ-2"])

            (tests / "REQ-2.spec.ts").write_text("test('REQ-2 persisted flow', async () => {});", encoding="utf-8")
            result = github_eval.preflight("hackathon--github", root / "arc")

        self.assertEqual(result["atomic_count"], 2)
        self.assertEqual(result["covered_count"], 2)
        self.assertEqual(result["spec_count"], 2)

    def test_preflight_rejects_unknown_spec_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            req = root / "arcbench-hackathon-requirements" / "hackathon--sheet" / "requirements.yaml"
            req.parent.mkdir(parents=True)
            req.write_text("id: ROOT\ntype: FOLDER\nchildren: [{id: REQ-1, type: ATOMIC}]\n", encoding="utf-8")
            tests = root / "arc" / "public-tests" / "hackathon--sheet"
            tests.mkdir(parents=True)
            (tests / "REQ-999.spec.ts").write_text("test('unknown', async () => {});", encoding="utf-8")

            result = github_eval.preflight("hackathon--sheet", root / "arc")
        self.assertEqual(result["uncovered"], ["REQ-1"])
        self.assertEqual(result["unknown_spec_files"], ["REQ-999.spec.ts"])

    def test_counts_damaged_scenario_text_without_rewriting_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.yaml"
            source = """id: ROOT
type: FOLDER
children:
  - id: REQ-1
    type: ATOMIC
    name: first
    dependencies: []
    scenarios:
      - name: damaged
        steps:
          - content: the requested workflow
"""
            requirements.write_text(source, encoding="utf-8")
            specs = root / "specs"
            specs.mkdir()

            report = github_eval.audit(requirements, specs)

            self.assertEqual(requirements.read_text(encoding="utf-8"), source)
        self.assertEqual(report["placeholder_occurrences"], 1)
        self.assertEqual(report["placeholder_occurrences_in_atomic_scenarios"], 1)
        self.assertEqual(len(report["degraded_scenarios"]), 1)

    def test_json_report_distinguishes_planned_mapping_from_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_dir = root / "task"
            task_dir.mkdir()
            requirements = task_dir / "requirements.yaml"
            requirements.write_text(
                """id: ROOT
type: FOLDER
children:
  - id: REQ-1
    type: ATOMIC
    name: first
    dependencies: []
    scenarios: []
""",
                encoding="utf-8",
            )
            result = {
                "requirements": str(requirements),
                "atomic_count": 1,
                "covered_count": 0,
                "spec_count": 0,
                "coverage_percent": 0,
                "placeholder_occurrences": 0,
                "placeholder_occurrences_in_atomic_scenarios": 0,
                "dependency_errors": [],
                "degraded_scenarios": [],
                "mapping": {"REQ-1": []},
                "uncovered": ["REQ-1"],
                "test_titles": {"REQ-1": []},
                "requirement_details": {"REQ-1": {
                    "name": "first", "description": "A sufficiently detailed requirement description.",
                    "dependencies": [], "scenario_count": 0, "description_usable": True,
                    "manual_review_required": True,
                }},
                "executed_count": None,
                "passed_count": None,
            }
            json_path, _ = github_eval.write_report(result, root / "audits")
            saved = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertIsNone(saved["executed_count"])
        self.assertIsNone(saved["passed_count"])


if __name__ == "__main__":
    unittest.main()
