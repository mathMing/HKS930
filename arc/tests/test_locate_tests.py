"""The bundle's own public specs are the fallback when the runner mounts none.

Submission 4224afbed824 (2026-09-26): all six official runs logged
`tests at None`, so every node was built and checked blind. The bundle now
ships public-tests/<task>/ and locate_tests picks the directory whose spec ids
cover this task's requirement tree.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main


def tree_for(task: str) -> dict:
    """The real requirement tree, so the spec-name parsing is checked against
    real node ids (`REQ-1.1.spec.ts` must count for node `REQ-1.1`)."""
    local_copy = main.BUNDLE_DIR / "tasks" / task
    path = local_copy if (local_copy / "requirements.yaml").is_file() else main.resolve_task_dir(task)
    return main.load_tree(path)


class LocateTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in ("ARCBENCH_TESTS_DIR", "OCTOS_ARC_LOCAL_TESTS", "OCTOS_ARC_BUNDLED_TESTS"):
            os.environ.pop(name, None)

    def test_picks_the_matching_bundled_task(self):
        for task in ("arc-bench-web--keep", "arc-bench-web--bookstack", "arc-bench-web--12306"):
            found = main.locate_tests(tree_for(task))
            self.assertEqual(found, (main.BUNDLE_DIR / "public-tests" / task).resolve(), task)

    def test_unknown_tree_stays_blind(self):
        tree = {"id": "ROOT", "type": "FOLDER", "children": [{"id": "XYZ-9.9", "type": "ATOMIC"}]}
        self.assertIsNone(main.locate_tests(tree))

    def test_bundled_fallback_can_be_switched_off(self):
        os.environ["OCTOS_ARC_BUNDLED_TESTS"] = "0"
        self.assertIsNone(main.locate_tests(tree_for("arc-bench-web--keep")))

    def test_runner_mount_still_wins(self):
        mount = main.BUNDLE_DIR / "public-tests" / "arc-bench-web--bookstack"
        os.environ["ARCBENCH_TESTS_DIR"] = str(mount)
        self.assertEqual(main.locate_tests(tree_for("arc-bench-web--keep")), Path(mount).resolve())

    def test_hackathon_spec_ids_drop_the_filename_separator_period(self):
        tree = tree_for("hackathon--github")
        nodes = [str(node["id"]) for node in main.atomic_nodes(tree)]
        tests = main.BUNDLE_DIR / "public-tests" / "hackathon--github"

        mapping = main.map_specs(tests, nodes)

        self.assertEqual(sum(len(files) for files in mapping.values()),
                         len(list(tests.glob("*.spec.ts"))))
        self.assertEqual(mapping["REQ-1-1-1"], ["REQ-1-1-1.spec.ts"])
        self.assertEqual(mapping["REQ-6-5"], ["REQ-6-5.spec.ts"])

    def test_sheet_selects_its_24_specs_not_the_overlapping_github_specs(self):
        tree = tree_for("hackathon--sheet")
        self.assertEqual(main.identify_hackathon_task(tree), "hackathon--sheet")
        found = main.locate_tests(tree)
        self.assertEqual(found, (main.BUNDLE_DIR / "public-tests" / "hackathon--sheet").resolve())
        ids = [str(node["id"]) for node in main.atomic_nodes(tree)]
        mapping = main.map_specs(found, ids)
        self.assertEqual(sum(bool(mapping[node_id]) for node_id in ids), 24)

    def test_partial_runner_mount_falls_back_to_complete_sheet_mirror(self):
        tree = tree_for("hackathon--sheet")
        with tempfile.TemporaryDirectory() as directory:
            mount = Path(directory)
            for source in list((main.BUNDLE_DIR / "public-tests" / "hackathon--sheet").glob("*.spec.ts"))[:13]:
                (mount / source.name).write_text("test('present', () => {});", encoding="utf-8")
            os.environ["ARCBENCH_TESTS_DIR"] = str(mount)
            found = main.locate_tests(tree)
        self.assertEqual(found, (main.BUNDLE_DIR / "public-tests" / "hackathon--sheet").resolve())

    def test_complete_runner_mount_remains_preferred(self):
        tree = tree_for("hackathon--sheet")
        with tempfile.TemporaryDirectory() as directory:
            mount = Path(directory)
            for source in (main.BUNDLE_DIR / "public-tests" / "hackathon--sheet").glob("*.spec.ts"):
                (mount / source.name).write_text("test('present', () => {});", encoding="utf-8")
            os.environ["ARCBENCH_TESTS_DIR"] = str(mount)
            found = main.locate_tests(tree)
            self.assertEqual(found, mount.resolve())

    def test_unrecognized_spec_id_is_not_silently_assigned(self):
        tree = {"id": "ROOT", "type": "FOLDER", "children": [
            {"id": "REQ-1", "type": "ATOMIC"},
            {"id": "REQ-2", "type": "ATOMIC"},
        ]}
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "REQ-999.spec.ts").write_text(
                "import { test } from '@playwright/test'; test('unknown id', () => {});",
                encoding="utf-8")
            mapping = main.map_specs(Path(directory), ["REQ-1", "REQ-2"])

        self.assertEqual(mapping, {"REQ-1": [], "REQ-2": []})

    def test_missing_tests_directory_returns_empty_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            mapping = main.map_specs(None, ["REQ-1"])

        self.assertEqual(mapping, {"REQ-1": []})

    def test_hackathon_preflight_rejects_spec_without_test_declaration(self):
        with tempfile.TemporaryDirectory() as directory:
            tests = Path(directory)
            (tests / "REQ-1.spec.ts").write_text("// intentionally empty", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no test\\(\\) declarations"):
                main.validate_spec_files_have_tests(
                    "hackathon--github", tests, {"REQ-1": ["REQ-1.spec.ts"]})


if __name__ == "__main__":
    unittest.main()
