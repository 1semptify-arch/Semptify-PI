"""Pytest fixtures for Semptify-PI tests."""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from collections.abc import Generator

import httpx
import mock_core.main as main
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_mock_state() -> None:
    """Clear in-memory token state before every test."""
    main.tokens_by_raw.clear()
    main.tokens_by_id.clear()
    main.pairing_codes.clear()


@pytest.fixture
def client() -> TestClient:
    """Sync TestClient for the mock_core app."""
    return TestClient(main.app)


@pytest.fixture(scope="session")
def live_mock_server() -> Generator[str, None, None]:
    """Start mock_core on a free port for tests that need a real HTTP socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_core.main:app", "--port", str(port), "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    deadline = time.monotonic() + 10
    base_url = f"http://127.0.0.1:{port}"
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{base_url}/api/v1/plugins", timeout=0.5)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("mock_core did not start for live test")

    try:
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
