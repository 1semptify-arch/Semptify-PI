"""Tests for the browser_extension reference plugin.

The JS client is exercised against a live mock_core server via Node. This
proves the provider-differentiated contract works from the browser-extension
client code without requiring a full browser automation harness.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

LIVE_SESSION_TOKEN = "sess_test"


def _load_manifest() -> dict[str, Any]:
    manifest_path = Path(__file__).parent.parent / "browser_extension" / "manifest.json"
    with open(manifest_path, encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def test_browser_extension_manifest_exists_and_valid() -> None:
    manifest = _load_manifest()
    assert manifest["manifest_version"] == 3
    assert manifest["name"]
    assert manifest["version"]
    assert "storage" in manifest["permissions"]
    assert manifest["background"]["service_worker"].endswith(".mjs")


def test_browser_extension_client_round_trip(live_mock_server: str) -> None:
    """Run the Node test runner against the live mock_core."""
    node = shutil.which("node")
    assert node, "node executable not found on PATH"

    repo_root = Path(__file__).parent.parent
    test_script = repo_root / "browser_extension" / "test-node.mjs"
    assert test_script.exists(), "browser_extension/test-node.mjs missing"

    env = os.environ.copy()
    env["CORE_URL"] = live_mock_server
    env["SESSION_TOKEN"] = LIVE_SESSION_TOKEN
    env["NODE_NO_WARNINGS"] = "1"

    result = subprocess.run(
        [node, str(test_script)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env=env,
    )

    print("--- stdout ---")
    print(result.stdout)
    if result.stderr:
        print("--- stderr ---")
        print(result.stderr)

    assert result.returncode == 0, f"browser_extension Node tests failed:\n{result.stderr}"
    assert "All browser_extension tests passed." in result.stdout
