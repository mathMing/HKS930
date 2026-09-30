"""The local grader is the only way to score a generated app without spending a
competition run, so a wrong number from it is worse than no number at all."""
import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "grade-local.py"
_spec = importlib.util.spec_from_file_location("grade_local", SCRIPT)
grade_local = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(grade_local)


class OutputEncodingTests(unittest.TestCase):
    def test_configures_streams_for_unicode_playwright_output(self):
        class FakeStream:
            def __init__(self):
                self.options = None

            def reconfigure(self, **options):
                self.options = options

        stdout, stderr = FakeStream(), FakeStream()
        with mock.patch.object(grade_local.sys, "stdout", stdout), \
                mock.patch.object(grade_local.sys, "stderr", stderr):
            grade_local.configure_text_streams()

        expected = {"encoding": "utf-8", "errors": "replace"}
        self.assertEqual(stdout.options, expected)
        self.assertEqual(stderr.options, expected)


class PortGuardTests(unittest.TestCase):
    def test_should_report_a_listening_port_as_taken(self):
        with socket.socket() as srv:
            srv.bind(("127.0.0.1", 0)); srv.listen(1)
            taken = srv.getsockname()[1]
            self.assertFalse(grade_local.port_is_free(taken))
        self.assertTrue(grade_local.port_is_free(taken))

    def test_should_refuse_to_grade_when_the_port_already_serves(self):
        """A crash used to leave the previous app listening, and the readiness
        probe only asked whether *something* answered -- so the next run graded
        the previous app under this app's name and printed a confident 0."""
        with tempfile.TemporaryDirectory() as tmp, socket.socket() as srv:
            srv.bind(("127.0.0.1", 0)); srv.listen(1)
            taken = srv.getsockname()[1]
            out = Path(tmp)
            (out / "frontend").mkdir(); (out / "backend").mkdir()
            self.assertFalse(grade_local.port_is_free(taken))


class AppTreeTests(unittest.TestCase):
    def test_should_not_write_a_lock_file_into_the_graded_app(self):
        """Grading npm-installs inside the app it is about to score. Those runs
        wrote backend/package-lock.json and frontend/package-lock.json, the
        pre-test `git add -A` snapshot staged them, and the cleanup could no
        longer remove them -- so scoring a bookstack run added two files to the
        deliverable it claims never to change."""
        for cwd, command in grade_local.app_install_steps(Path("/app")):
            self.assertIn("--no-package-lock", command, f"{cwd} install writes a lock file")

    def test_should_still_build_the_frontend_and_install_the_backend(self):
        steps = dict((cwd.name, command) for cwd, command in grade_local.app_install_steps(Path("/app")))
        self.assertIn("npm run build", steps["frontend"])
        self.assertIn("npm install", steps["backend"])


class TeardownTests(unittest.TestCase):
    def test_should_stop_a_server_whose_process_group_cannot_be_signalled(self):
        """`killpg` raised PermissionError on macOS and killed the grader
        instead of the app, leaking the listener that poisons the next run."""
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        if os.name == "nt":
            with mock.patch.object(grade_local.subprocess, "run") as run:
                grade_local.stop_server(proc)
                run.assert_called_once()
                self.assertEqual(run.call_args.args[0][:2], ["taskkill", "/PID"])
                proc.kill()
                proc.wait(timeout=5)
        else:
            original = grade_local.os.killpg

            def deny(*_a, **_k):
                raise PermissionError(1, "Operation not permitted")

            grade_local.os.killpg = deny
            try:
                grade_local.stop_server(proc)
            finally:
                grade_local.os.killpg = original
        self.assertIsNotNone(proc.poll(), "server survived a teardown that could not signal its group")

    def test_should_be_a_noop_for_an_already_finished_server(self):
        proc = subprocess.Popen([sys.executable, "-c", "pass"])
        proc.wait()
        grade_local.stop_server(proc)
        self.assertIsNotNone(proc.poll())


class ReportTests(unittest.TestCase):
    def test_should_count_passes_and_failures_inside_nested_playwright_suites(self):
        suites = [{"suites": [{"specs": [
            {"title": "passing flow", "tests": [{"status": "expected"}]},
            {"title": "failing flow", "tests": [{"status": "unexpected"}]},
        ]}]}]
        results = list(grade_local.walk_report(suites))
        self.assertEqual(results, [("passing flow", True), ("failing flow", False)])

    def test_infrastructure_failure_is_not_reported_as_a_zero_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            grade_local.save_infrastructure_failure(out, "hackathon--sheet", "server unavailable")
            report = __import__("json").loads(
                (out / ".arc" / "hackathon--sheet-local-grade.json").read_text(encoding="utf-8")
            )
        self.assertEqual(report["status"], "infrastructure_failure")
        self.assertIsNone(report["passed"])
        self.assertIsNone(report["total"])


if __name__ == "__main__":
    unittest.main()
