import unittest
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import verify_node


class PlaywrightCommandTests(unittest.TestCase):
    def test_uses_node_with_the_playwright_cli_on_all_platforms(self):
        root = Path(r"X:\local grader")
        node = r"C:\Program Files\nodejs\node.exe"
        env = {"PATH": r"C:\Program Files\nodejs"}
        with patch.object(verify_node.shutil, "which", return_value=node):
            command = verify_node.playwright_command(root, env, "test", "--list")

        self.assertEqual(command, [
            node,
            str(root / "node_modules" / "@playwright" / "test" / "cli.js"),
            "test", "--list",
        ])


class OutputEncodingTests(unittest.TestCase):
    def test_configures_stdout_and_stderr_for_unicode_reporter_output(self):
        class FakeStream:
            def __init__(self):
                self.options = None

            def reconfigure(self, **options):
                self.options = options

        stdout, stderr = FakeStream(), FakeStream()
        with patch.object(verify_node.sys, "stdout", stdout), \
                patch.object(verify_node.sys, "stderr", stderr):
            verify_node.configure_text_streams()

        expected = {"encoding": "utf-8", "errors": "replace"}
        self.assertEqual(stdout.options, expected)
        self.assertEqual(stderr.options, expected)


class ProgressMarkerTests(unittest.TestCase):
    def test_marker_records_phase_without_paths_or_secrets(self):
        with tempfile.TemporaryDirectory() as scratch:
            with patch.object(verify_node.Path, "cwd", return_value=Path(scratch)):
                verify_node.mark_progress("run-playwright")
            marker = json.loads((Path(scratch) / ".arc-verify-progress.json").read_text())
        self.assertEqual(marker["phase"], "run-playwright")
        self.assertEqual(set(marker), {"phase", "at", "pid"})


class VerifierArgumentTests(unittest.TestCase):
    def test_accepts_playwright_root_before_required_positionals(self):
        argv = [
            "--playwright-root", r"X:\local grader",
            r"X:\tests", "43100",
            "--tag", "REQ-1-1-1", "--attempts", "6",
            "REQ-1-1-1.spec.ts",
        ]

        opts, positional = verify_node.parse_arguments(argv)

        self.assertEqual(opts, {"playwright-root": r"X:\local grader",
                                "tag": "REQ-1-1-1", "attempts": "6"})
        self.assertEqual(positional, [r"X:\tests", "43100", "REQ-1-1-1.spec.ts"])

    def test_rejects_options_without_values(self):
        with self.assertRaisesRegex(ValueError, "missing value for --tag"):
            verify_node.parse_arguments([r"X:\tests", "43100", "--tag"])


class WindowsTeardownTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows process-tree behavior")
    def test_kills_npm_and_node_descendants_with_taskkill_tree(self):
        class FakeProcess:
            pid = 12345

            def __init__(self):
                self.stopped = False

            def poll(self):
                return None if not self.stopped else 0

            def wait(self, timeout=None):
                self.stopped = True
                return 0

            def terminate(self):
                self.stopped = True

            def kill(self):
                self.stopped = True

        proc = FakeProcess()
        with patch.object(verify_node.subprocess, "run") as run:
            verify_node.stop(proc)

        self.assertEqual(run.call_args.args[0], ["taskkill", "/PID", "12345", "/T", "/F"])
        self.assertTrue(proc.stopped)


if __name__ == "__main__":
    unittest.main()
