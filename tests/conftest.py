"""Pytest fixtures for Semptify-PI tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import mock_core.main as main


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
