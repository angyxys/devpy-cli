from __future__ import annotations

import urllib.request
import json

from devpy import __version__


def get_version() -> str:
    return __version__


def fetch_latest_version() -> str | None:
    try:
        url = "https://pypi.org/pypi/devpy-cli/json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("info", {}).get("version")
    except Exception:
        return None


def _parse_version(v: str) -> tuple[int, ...]:
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def check_for_update() -> str | None:
    latest = fetch_latest_version()
    if not latest:
        return None
    current = get_version()
    if _parse_version(latest) > _parse_version(current):
        return f"Update available: {current} -> {latest}. Run: pip install --upgrade devpy-cli"
    return None
