import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "contest-local.py"
spec = importlib.util.spec_from_file_location("contest_local", SCRIPT)
contest_local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contest_local)


class OrderedContestRunnerTests(unittest.TestCase):
    def test_only_a_finished_pipeline_allows_next_stage(self):
        with tempfile.TemporaryDirectory() as scratch:
            output = Path(scratch)
            report = output / ".arc" / "run-summary.json"
            self.assertFalse(contest_local.completed_pipeline(output))
            report.parent.mkdir()
            report.write_text(json.dumps({"success": False, "pipeline_completed": False}))
            self.assertFalse(contest_local.completed_pipeline(output))
            report.write_text(json.dumps({"success": False, "pipeline_completed": True}))
            self.assertTrue(contest_local.completed_pipeline(output))

    def test_interrupted_github_stops_before_grading_or_sheet(self):
        with mock.patch.object(contest_local.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
            with mock.patch.object(contest_local, "completed_pipeline", return_value=False):
                with mock.patch.object(sys, "argv", [str(SCRIPT), "--name", "unit-test"]):
                    code = contest_local.main()
        self.assertEqual(code, 7)
        self.assertEqual(run.call_count, 1)

    def test_check_mode_preflights_github_then_sheet_without_model_runs(self):
        with mock.patch.object(contest_local.subprocess, "run",
                               side_effect=[mock.Mock(returncode=0), mock.Mock(returncode=0)]) as run:
            with mock.patch.object(sys, "argv", [str(SCRIPT), "--check"]):
                code = contest_local.main()
        self.assertEqual(code, 0)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 2)
        self.assertIn("hackathon--github", commands[0])
        self.assertIn("hackathon--sheet", commands[1])
        self.assertTrue(all("--preflight" in command for command in commands))

    def test_failure_in_second_run_stops_before_its_grading_and_reports_order(self):
        metrics = json.dumps({"duration_s": 4, "cost": 0.1, "grade": "1/1"})
        results = [
            mock.Mock(returncode=0),  # GitHub model run
            mock.Mock(returncode=0),  # GitHub local grade
            mock.Mock(returncode=0, stdout=metrics),  # GitHub metrics
            mock.Mock(returncode=7),  # Spreadsheet model run fails
        ]
        with mock.patch.object(contest_local.subprocess, "run", side_effect=results) as run:
            with mock.patch.object(contest_local, "completed_pipeline", return_value=True):
                with mock.patch.object(sys, "argv", [str(SCRIPT), "--name", "unit-test"]):
                    code = contest_local.main()

        self.assertEqual(code, 7)
        calls = [call.args[0] for call in run.call_args_list]
        self.assertIn("hackathon--github", calls[0])
        self.assertIn("hackathon--github", calls[1])
        self.assertIn("hackathon--sheet", calls[3])
        self.assertNotIn("grade-local.py", calls[3])
        self.assertEqual(len(calls), 4)


if __name__ == "__main__":
    unittest.main()
