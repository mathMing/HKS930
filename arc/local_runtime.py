"""Small local-runtime environment helpers for Windows ARC runs."""
from __future__ import annotations

import os
from pathlib import Path


def add_windows_shell_path(env: dict[str, str], candidates: tuple[Path, ...] = (
        Path(r"X:\MINGW\w64devkit\bin"),)) -> dict[str, str]:
    """Return an env copy with a directory containing sh.exe available on PATH."""
    result = dict(env)
    entries = result.get("PATH", "").split(os.pathsep)
    for directory in candidates:
        if (directory / "sh.exe").is_file() and str(directory) not in entries:
            result["PATH"] = str(directory) + (os.pathsep + result["PATH"] if result.get("PATH") else "")
            break
    return result
