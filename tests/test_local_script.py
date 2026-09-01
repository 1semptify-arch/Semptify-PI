"""Tests for the local_script reference plugin."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import mock_core.main as main
from local_script.client import SemptifyPluginClient
from local_script.config import PluginConfig


SESSION_TOKEN = "sess_synthetic"


def test_config_save_and_load(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    config = PluginConfig(
        core_url="http://testserver",
        plugin_id="example-document-organizer",
        plugin_token="pl_test",
    )
    config.to_file(path)
    loaded = PluginConfig.from_file(path)
    assert loaded.core_url == "http://testserver"
    assert loaded.plugin_id == "example-document-organizer"
    assert loaded.plugin_token == "pl_test"


def test_config_apply_env(monkeypatch) -> None:
    monkeypatch.setenv("SEMPIFY_PI_CORE_URL", "http://env-server")
    monkeypatch.setenv("SEMPIFY_PI_PLUGIN_ID", "env-plugin")
    monkeypatch.setenv("SEMPIFY_PI_PLUGIN_TOKEN", "env-token")
    config = PluginConfig.from_file(None).apply_env()
    assert config.core_url == "http://env-server"
    assert config.plugin_id == "env-plugin"
    assert config.plugin_token == "env-token"


def test_list_plugins(client: TestClient) -> None:
    pi_client = SemptifyPluginClient(core_url="http://testserver", client=client)
    data = pi_client.list_plugins()
    assert "plugins" in data
    plugin_ids = {p["plugin_id"] for p in data["plugins"]}
    assert "example-document-organizer" in plugin_ids
    assert "case-packet-builder" in plugin_ids

    data = pi_client.list_plugins(packaging="local_script")
    plugin_ids = {p["plugin_id"] for p in data["plugins"]}
    assert "example-document-organizer" in plugin_ids


def test_get_plugin(client: TestClient) -> None:
    pi_client = SemptifyPluginClient(core_url="http://testserver", client=client)
    manifest = pi_client.get_plugin("example-document-organizer")
    assert manifest["plugin_id"] == "example-document-organizer"
    assert manifest["status"] == "approved"


def _connect(
    client: TestClient, plugin_id: str = "example-document-organizer"
) -> str:
    pi_client = SemptifyPluginClient(core_url="http://testserver", client=client)
    result = pi_client.connect(
        plugin_id=plugin_id,
        session_token=SESSION_TOKEN,
        packaging="local_script",
        label="test client",
    )
    assert "token" in result
    assert result["plugin_id"] == plugin_id
    assert result["packaging"] == "local_script"
    assert "vault:read" in result["scopes"]
    return result["token"]


def _download_capability(
    client: TestClient, token: str, file_id: str, provider: str = "google_drive"
) -> dict:
    r = client.post(
        f"/api/v1/plugin/files/{file_id}/download-url",
        params={"provider": provider},
        headers={"Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    return r.json()


def _upload_capability(
    client: TestClient,
    token: str,
    filename: str,
    parent_folder: str | None = None,
    provider: str = "google_drive",
) -> dict:
    body: dict[str, str] = {"filename": filename}
    if parent_folder:
        body["parent_folder"] = parent_folder
    r = client.post(
        "/api/v1/plugin/files/upload-url",
        params={"provider": provider},
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    r.raise_for_status()
    return r.json()


def test_connect_and_me(client: TestClient) -> None:
    token = _connect(client)
    pi_client = SemptifyPluginClient(
        core_url="http://testserver", plugin_token=token, client=client
    )
    me = pi_client.me()
    assert me["plugin_id"] == "example-document-organizer"
    assert me["packaging"] == "local_script"
    assert "vault:read" in me["effective_scopes"]


@pytest.mark.parametrize("provider", ["google_drive", "dropbox", "onedrive"])
def test_download_url_by_provider(client: TestClient, provider: str) -> None:
    token = _connect(client)
    result = _download_capability(client, token, "doc_123", provider=provider)
    assert "expires_at" in result

    if provider == "google_drive":
        assert "direct_request" in result
        assert "download_url" not in result
        dr = result["direct_request"]
        assert dr["endpoint"].startswith("https://www.googleapis.com/drive/v3/files/")
        assert dr["method"] == "GET"
        assert dr["query"]["alt"] == "media"
        assert dr["headers"]["Authorization"].startswith("Bearer ")
    else:
        assert "download_url" in result
        assert "direct_request" not in result
        if provider == "dropbox":
            assert "dl.dropboxusercontent.com" in result["download_url"]
        else:
            assert "1drv.com" in result["download_url"]


@pytest.mark.parametrize("provider", ["google_drive", "dropbox", "onedrive"])
def test_upload_url_by_provider(client: TestClient, provider: str) -> None:
    token = _connect(client)
    upload = _upload_capability(
        client, token, "notice.pdf", parent_folder="/Semptify5.0/Inbox", provider=provider
    )
    assert "completion_token" in upload
    assert "expires_at" in upload

    if provider == "google_drive":
        assert "direct_request" in upload
        assert "upload_url" not in upload
        dr = upload["direct_request"]
        assert dr["endpoint"] == "https://www.googleapis.com/upload/drive/v3/files"
        assert dr["method"] == "POST"
        assert dr["query"]["uploadType"] == "resumable"
        assert dr["body"]["name"] == "notice.pdf"
        assert dr["body"]["parents"] == ["/Semptify5.0/Inbox"]
        assert "Authorization" in dr["headers"]
        assert "Content-Type" in dr["headers"]
    elif provider == "dropbox":
        assert "direct_request" in upload
        assert "upload_url" not in upload
        dr = upload["direct_request"]
        assert dr["endpoint"] == "https://content.dropboxapi.com/2/files/upload"
        assert dr["method"] == "POST"
        assert "Authorization" in dr["headers"]
        assert "Dropbox-API-Arg" in dr["headers"]
    else:
        assert "upload_url" in upload
        assert "direct_request" not in upload
        assert "1drv.com" in upload["upload_url"]


def test_complete_upload(client: TestClient) -> None:
    token = _connect(client)
    upload = _upload_capability(client, token, "notice.pdf", parent_folder="/Semptify5.0/Inbox")
    completed = SemptifyPluginClient(
        core_url="http://testserver", plugin_token=token, client=client
    ).complete_upload(
        completion_token=upload["completion_token"],
        provider_file_id="provider_abc",
        filename="notice.pdf",
        size=1024,
    )
    assert completed["filename"] == "notice.pdf"
    assert completed["vault_path"] == "/Semptify5.0/Inbox/notice.pdf"
    assert completed["provider_file_id"] == "provider_abc"
    assert completed["size"] == 1024
    assert completed["file_id"].startswith("f_")


def test_cli_connect(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    import local_script.client as client_module
    from local_script import semptify_plugin
    from local_script.semptify_plugin import main as cli_main

    class TestPluginClient(client_module.SemptifyPluginClient):
        def __init__(self, core_url: str, plugin_token: str | None = None) -> None:
            client_module.SemptifyPluginClient.__init__(
                self, core_url, plugin_token, client=client
            )

        def close(self) -> None:
            pass

    monkeypatch.setattr(semptify_plugin, "SemptifyPluginClient", TestPluginClient)

    config_path = tmp_path / "config.json"
    monkeypatch.setenv("SEMPIFY_PI_SESSION_TOKEN", SESSION_TOKEN)
    exit_code = cli_main(
        [
            "--config",
            str(config_path),
            "connect",
            "example-document-organizer",
            "--packaging",
            "local_script",
        ]
    )
    assert exit_code == 0
    assert config_path.exists()
    data = json.loads(config_path.read_text())
    assert data["plugin_id"] == "example-document-organizer"
    assert data["plugin_token"].startswith("pl_")
