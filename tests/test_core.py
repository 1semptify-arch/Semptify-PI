"""Tests for the Semptify-PI real Core token and containment layer."""
from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from core import main
from core.database import Database


@pytest.fixture
def core_client(tmp_path: Path, monkeypatch) -> Generator[TestClient, None, None]:
    """Create a TestClient against the real Core with a fresh in-memory DB."""
    # Use a file-backed sqlite test db so each client is isolated.
    db_path = tmp_path / "core_test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    db = Database(db_url)
    main.state = main.CoreState(database=db)

    with TestClient(main.app) as client:
        yield client

    # Reset state to avoid leaking the temp db across tests.
    main.state = main.CoreState()


SESSION = "sess_test_tenant_a"
OTHER_SESSION = "sess_test_tenant_b"


def _auth(client: TestClient, token: str | None, method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.request(method, path, headers=headers, **kwargs)


def test_connect_and_me(core_client: TestClient):
    res = core_client.post(
        "/api/v1/plugins/example-document-organizer/connect",
        json={"packaging": "local_script"},
        headers={"Authorization": f"Bearer {SESSION}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["token"].startswith("pl_")
    assert data["plugin_id"] == "example-document-organizer"
    assert "vault:read" in data["scopes"]

    me = _auth(core_client, data["token"], "GET", "/api/v1/plugin/me")
    assert me.status_code == 200
    assert me.json()["user_id"] == SESSION


def test_revoke_token_rejected_next_use(core_client: TestClient):
    res = core_client.post(
        "/api/v1/plugins/example-document-organizer/connect",
        json={"packaging": "local_script"},
        headers={"Authorization": f"Bearer {SESSION}"},
    )
    data = res.json()
    token = data["token"]
    token_id = data["token_id"]

    # Revoke via session auth.
    revoke = core_client.delete(
        f"/api/v1/plugins/tokens/{token_id}",
        headers={"Authorization": f"Bearer {SESSION}"},
    )
    assert revoke.status_code == 204

    # Next use must fail immediately.
    me = _auth(core_client, token, "GET", "/api/v1/plugin/me")
    assert me.status_code == 401


def test_per_file_tenant_validation(core_client: TestClient):
    # Tenant A connects and records a file.
    a = core_client.post(
        "/api/v1/plugins/example-document-organizer/connect",
        json={"packaging": "local_script"},
        headers={"Authorization": f"Bearer {SESSION}"},
    ).json()

    complete = core_client.post(
        "/api/v1/plugin/files/complete",
        json={
            "completion_token": "cpl_abc",
            "provider_file_id": "provider_123",
            "filename": "notice_a.pdf",
            "size": 1024,
        },
        headers={"Authorization": f"Bearer {a['token']}"},
    )
    assert complete.status_code == 200
    file_id = complete.json()["file_id"]

    # Tenant B connects and tries to download Tenant A's file.
    b = core_client.post(
        "/api/v1/plugins/example-document-organizer/connect",
        json={"packaging": "local_script"},
        headers={"Authorization": f"Bearer {OTHER_SESSION}"},
    ).json()

    dl = _auth(
        core_client,
        b["token"],
        "POST",
        f"/api/v1/plugin/files/{file_id}/download-url?provider=google_drive",
    )
    assert dl.status_code == 403


def test_dropbox_upload_containment(core_client: TestClient):
    token = core_client.post(
        "/api/v1/plugins/example-document-organizer/connect",
        json={"packaging": "local_script"},
        headers={"Authorization": f"Bearer {SESSION}"},
    ).json()["token"]

    # Path-escape attempt.
    res = _auth(
        core_client,
        token,
        "POST",
        "/api/v1/plugin/files/upload-url?provider=dropbox",
        json={"filename": "../../etc/passwd"},
    )
    assert res.status_code == 400


def test_onedrive_upload_containment_and_folder(core_client: TestClient):
    token = core_client.post(
        "/api/v1/plugins/example-document-organizer/connect",
        json={"packaging": "local_script"},
        headers={"Authorization": f"Bearer {SESSION}"},
    ).json()["token"]

    # Normal upload lands inside the vault folder.
    res = _auth(
        core_client,
        token,
        "POST",
        "/api/v1/plugin/files/upload-url?provider=onedrive",
        json={"filename": "notice.pdf"},
    )
    assert res.status_code == 200
    assert res.json()["completion_token"]

    # Escape attempt rejected.
    bad = _auth(
        core_client,
        token,
        "POST",
        "/api/v1/plugin/files/upload-url?provider=onedrive",
        json={"filename": "../../../outside.pdf"},
    )
    assert bad.status_code == 400


def test_complete_upload_containment(core_client: TestClient):
    token = core_client.post(
        "/api/v1/plugins/example-document-organizer/connect",
        json={"packaging": "local_script"},
        headers={"Authorization": f"Bearer {SESSION}"},
    ).json()["token"]

    # Outside the vault folder.
    bad = core_client.post(
        "/api/v1/plugin/files/complete",
        json={
            "completion_token": "cpl_abc",
            "provider_file_id": "p123",
            "filename": "x.pdf",
            "vault_path": "/Outside/Semptify5.0/Inbox/x.pdf",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bad.status_code == 400

    # Inside the vault folder.
    good = core_client.post(
        "/api/v1/plugin/files/complete",
        json={
            "completion_token": "cpl_def",
            "provider_file_id": "p456",
            "filename": "notice.pdf",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert good.status_code == 200
    assert good.json()["vault_path"].startswith("/Semptify5.0/Inbox")
