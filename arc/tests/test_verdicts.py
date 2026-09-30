import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import main
import verify_node


class VerifierVerdicts(unittest.TestCase):
    def setUp(self):
        self.previous = dict(verify_node.VERDICT)
        self.addCleanup(lambda: verify_node.VERDICT.update(self.previous))

    def test_unique_results_and_secret_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(verify_node.Path, "cwd", return_value=root), \
                    mock.patch.dict(os.environ, {"OPENAI_API_KEY": "secret-credential-123"}):
                verify_node.VERDICT.update(phase="run-playwright", category="application_failure",
                                            reason="playwright_failed", detail="Bearer abc123 secret-credential-123")
                verify_node.write_verdict("REQ-1", 1, 0.25, 1)
                verify_node.write_verdict("REQ-1", 2, 0.30, 1)
                files = list((root / ".arc-verify-results").glob("*.json"))
                self.assertEqual(len(files), 2)
                data = [json.loads(file.read_text()) for file in files]
                self.assertEqual({item["attempt"] for item in data}, {1, 2})
                self.assertTrue(all(item["category"] == "application_failure" for item in data))
                self.assertTrue(all("secret-credential-123" not in item["detail"] for item in data))
                self.assertTrue(all("abc123" not in item["detail"] for item in data))

    def test_pass_is_separate_from_previous_failure(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(verify_node.Path, "cwd", return_value=Path(directory)):
            verify_node.VERDICT.update(category="infrastructure_failure", reason="port_busy", detail="old")
            verify_node.write_verdict("REQ-2", 1, 0.1, 0)
            event = json.loads(next((Path(directory) / ".arc-verify-results").glob("*.json")).read_text())
            self.assertEqual((event["category"], event["reason"], event["detail"]), ("pass", "passed", ""))

    def test_missing_node_is_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(verify_node.Path, "cwd", return_value=Path(directory)), \
                mock.patch.object(verify_node.shutil, "which", return_value=None):
            (Path(directory) / "frontend" / "src").mkdir(parents=True)
            rc = verify_node.check(Path(directory), 43100, ["REQ-1.spec.ts"])
            self.assertEqual(rc, 1)
            self.assertEqual((verify_node.VERDICT["category"], verify_node.VERDICT["reason"]),
                             ("infrastructure_failure", "node_missing"))

    def test_build_failure_is_application_failure(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(verify_node, "sh", return_value=(1, "build syntax error")), \
                mock.patch.object(verify_node, "mark_progress"):
            app = Path(directory)
            self.assertEqual(verify_node.run_app(app, app, {}, app, 43100, ["REQ-1.spec.ts"]), 1)
            self.assertEqual((verify_node.VERDICT["category"], verify_node.VERDICT["reason"]),
                             ("application_failure", "build_failed"))

    def test_port_conflict_is_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(verify_node, "sh", return_value=(0, "")), \
                mock.patch.object(verify_node, "free", return_value=False), \
                mock.patch.object(verify_node, "mark_progress"):
            app = Path(directory)
            self.assertEqual(verify_node.run_app(app, app, {}, app, 43100, ["REQ-1.spec.ts"]), 1)
            self.assertEqual((verify_node.VERDICT["category"], verify_node.VERDICT["reason"]),
                             ("infrastructure_failure", "port_busy"))

    def test_browser_absence_and_assertion_failure_are_distinct(self):
        class FakeServer:
            def poll(self):
                return None

        for log, category, reason in (
                (verify_node.NO_BROWSER, "infrastructure_failure", "browser_unavailable"),
                ("Error: expect(locator).toBeVisible()", "application_failure", "playwright_failed")):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with mock.patch.object(verify_node, "sh", side_effect=[(0, ""), (0, ""), (1, log)]), \
                        mock.patch.object(verify_node, "free", side_effect=[True, False, False]), \
                        mock.patch.object(verify_node, "playwright_root", return_value=(root, {})), \
                        mock.patch.object(verify_node, "install_browser", return_value=False), \
                        mock.patch.object(verify_node.subprocess, "Popen", return_value=FakeServer()), \
                        mock.patch.object(verify_node, "stop"), \
                        mock.patch.object(verify_node, "mark_progress"):
                    self.assertNotEqual(verify_node.run_app(root, root, {}, root, 43100,
                                                            ["REQ-1.spec.ts"]), 0)
                    self.assertEqual((verify_node.VERDICT["category"], verify_node.VERDICT["reason"]),
                                     (category, reason))

    def test_infrastructure_failure_skips_repair_counter_and_status(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(verify_node.Path, "cwd", return_value=Path(directory)), \
                mock.patch.object(verify_node, "check", side_effect=lambda *_:
                                  verify_node.fail("infrastructure_failure", "playwright_unavailable", "missing")):
            rc = verify_node.main([directory, "43100", "--tag", "REQ-1"])
            self.assertEqual(rc, 1)
            self.assertFalse((Path(directory) / ".arc-status" / "REQ-1").exists())
            self.assertFalse((Path(directory) / ".arc-attempts" / "REQ-1").exists())
            event = json.loads(next((Path(directory) / ".arc-verify-results").glob("*.json")).read_text())
            self.assertEqual(event["category"], "infrastructure_failure")

    def test_repeated_application_failures_keep_both_attempt_results(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(verify_node.Path, "cwd", return_value=Path(directory)), \
                mock.patch.object(verify_node, "check", side_effect=lambda *_:
                                  verify_node.fail("application_failure", "playwright_failed", "assertion")):
            for _ in range(2):
                self.assertEqual(verify_node.main([directory, "43100", "--tag", "REQ-1"]), 1)
            files = (Path(directory) / ".arc-verify-results").glob("*.json")
            self.assertEqual({json.loads(path.read_text())["attempt"] for path in files}, {1, 2})
            self.assertEqual((Path(directory) / ".arc-attempts" / "REQ-1").read_text(), "2")

    def test_success_records_pass_and_verified_snapshot(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(verify_node.Path, "cwd", return_value=Path(directory)), \
                mock.patch.object(verify_node, "check", return_value=0):
            root = Path(directory)
            (root / "frontend" / "src").mkdir(parents=True)
            (root / "frontend" / "src" / "index.html").write_text("verified")
            (root / "backend").mkdir()
            (root / "backend" / "server.js").write_text("server")
            self.assertEqual(verify_node.main([directory, "43100", "--tag", "REQ-1"]), 0)
            event = json.loads(next((root / ".arc-verify-results").glob("*.json")).read_text())
            self.assertEqual(event["category"], "pass")
            self.assertEqual((root / ".arc-status" / "REQ-1").read_text(), "0")
            self.assertEqual((root / ".arc-good" / "app" / "frontend" / "src" / "index.html").read_text(),
                             "verified")


class AdapterVerdicts(unittest.TestCase):
    def test_fatal_result_is_surfaced_once_and_stops_wait(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, out = root / "data", root / "out"
            results = data / "profiles" / "p" / "data" / "pipeline-runs" / "arc_build-1" / ".arc-verify-results"
            results.mkdir(parents=True)
            (out / ".arc").mkdir(parents=True)
            event = {"tag": "REQ-1", "attempt": 1, "phase": "find-playwright", "rc": 1,
                     "category": "infrastructure_failure", "reason": "playwright_unavailable",
                     "elapsed_s": 0.2, "detail": "no runner"}
            (results / "1.json").write_text(json.dumps(event))
            seen = set()
            self.assertEqual(main.consume_verdicts(data, "arc_build", out, seen), event)
            self.assertIsNone(main.consume_verdicts(data, "arc_build", out, seen))
            self.assertEqual(len((out / ".arc" / "check-results.jsonl").read_text().splitlines()), 1)
            session = mock.Mock()
            state = {"started": time.time()}
            policy = {"name": "arc_build", "run_timeout": 60, "final_reserve_seconds": 0,
                      "verify_timeout": 10}
            self.assertEqual(main.wait_for_pipeline(session, state, policy, data, out), event)
            session._notifications.get.assert_not_called()

    def test_verified_only_collection_never_promotes_unchecked_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, out = root / "data", root / "out"
            run = data / "profiles" / "p" / "data" / "pipeline-runs" / "arc_build-1"
            (run / "frontend" / "src").mkdir(parents=True)
            (run / "frontend" / "src" / "index.html").write_text("unchecked")
            (out / "frontend" / "src").mkdir(parents=True)
            target = out / "frontend" / "src" / "index.html"
            target.write_text("existing")
            main.collect_app(data, out, "arc_build", verified_only=True)
            self.assertEqual(target.read_text(), "existing")
            good = run / ".arc-good" / "app"
            (good / "frontend" / "src").mkdir(parents=True)
            (good / "frontend" / "src" / "index.html").write_text("verified")
            (good / "backend").mkdir()
            main.collect_app(data, out, "arc_build", verified_only=True)
            self.assertEqual(target.read_text(), "verified")


if __name__ == "__main__":
    unittest.main()
