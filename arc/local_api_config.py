"""Safe local parsing for ARC/DeepSeek-compatible API credentials."""
from __future__ import annotations

import os
from pathlib import Path


def read_local_api_config(path: Path) -> dict[str, str]:
    """Read supported KEY=VALUE or KEY:VALUE entries without logging values."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            key, separator, value = line.partition(":")
        if separator and key.strip() in {"OPENAI_API_KEY", "OPENAI_BASE_URL", "ARCBENCH_API_KEY"}:
            values[key.strip()] = value.strip().strip("\"'")
    return values


def resolve_api_settings(env: dict[str, str] | None, path: Path) -> tuple[str | None, str]:
    """Select a key/base URL pair and prevent OpenAI keys reaching ARC by accident."""
    environ = os.environ if env is None else env
    local = read_local_api_config(path)
    platform_key = environ.get("ARCBENCH_API_KEY")
    base_url = environ.get("OPENAI_BASE_URL") or local.get("OPENAI_BASE_URL")
    if platform_key:
        key = platform_key
        base_url = base_url or "https://api.arc-bench.com/v1"
    elif base_url:
        key = environ.get("OPENAI_API_KEY") or local.get("OPENAI_API_KEY")
    else:
        key = None
        base_url = "https://api.arc-bench.com/v1"
    if key and base_url.rstrip("/").lower() == "https://api.arc-bench.com/v1" and not platform_key:
        raise ValueError("non-ARC key cannot be sent to the ARC endpoint")
    return key, base_url
