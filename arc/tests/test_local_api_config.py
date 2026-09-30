import tempfile
import unittest
from pathlib import Path

import local_api_config
import local_runtime


class LocalApiConfigTests(unittest.TestCase):
    def test_reads_equals_and_colon_syntax_without_chopping_url_scheme(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "api.txt"
            config.write_text("OPENAI_API_KEY=secret-placeholder\nOPENAI_BASE_URL:https://api.deepseek.com\n", encoding="utf-8")
            key, base_url = local_api_config.resolve_api_settings({}, config)
        self.assertEqual(key, "secret-placeholder")
        self.assertEqual(base_url, "https://api.deepseek.com")

    def test_requires_a_custom_base_url_before_using_openai_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "api.txt"
            config.write_text("OPENAI_API_KEY=secret-placeholder\n", encoding="utf-8")
            key, base_url = local_api_config.resolve_api_settings({}, config)
        self.assertIsNone(key)
        self.assertEqual(base_url, "https://api.arc-bench.com/v1")

    def test_does_not_send_an_openai_key_to_the_arc_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "api.txt"
            config.write_text("OPENAI_API_KEY=secret-placeholder\nOPENAI_BASE_URL=https://api.arc-bench.com/v1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-ARC key"):
                local_api_config.resolve_api_settings({}, config)

    def test_explicit_arc_key_defaults_to_arc_base_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            key, base_url = local_api_config.resolve_api_settings(
                {"ARCBENCH_API_KEY": "platform-placeholder"}, Path(tmp) / "missing.txt")
        self.assertEqual(key, "platform-placeholder")
        self.assertEqual(base_url, "https://api.arc-bench.com/v1")


class LocalRuntimeTests(unittest.TestCase):
    def test_adds_only_a_directory_that_contains_sh_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "sh.exe").touch()
            original = {"PATH": "existing-path"}
            result = local_runtime.add_windows_shell_path(original, (directory,))
        self.assertEqual(original["PATH"], "existing-path")
        self.assertTrue(result["PATH"].startswith(str(directory)))

    def test_does_not_change_path_when_no_shell_is_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = local_runtime.add_windows_shell_path({"PATH": "existing-path"}, (Path(tmp),))
        self.assertEqual(result["PATH"], "existing-path")

if __name__ == "__main__":
    unittest.main()
