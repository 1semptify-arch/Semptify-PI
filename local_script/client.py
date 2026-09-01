"""Semptify-PI local_script client — zero-transfer, scoped plugin token client."""
from __future__ import annotations

from typing import Any, cast

import httpx


class SemptifyPluginClient:
    """HTTP client that talks to the Semptify-PI plugin API.

    The client never handles document bytes. It requests scoped direct URLs
    from Core and passes them back to the caller.
    """

    def __init__(
        self,
        core_url: str,
        plugin_token: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.core_url = core_url.rstrip("/")
        self.plugin_token = plugin_token
        self._client = client or httpx.Client(base_url=self.core_url)

    def _plugin_headers(self) -> dict[str, str]:
        if not self.plugin_token:
            raise RuntimeError("No plugin token configured. Run 'connect' first.")
        return {"Authorization": f"Bearer {self.plugin_token}"}

    def list_plugins(self, packaging: str | None = None) -> dict[str, Any]:
        params = {"packaging": packaging} if packaging else None
        r = self._client.get("/api/v1/plugins", params=params)
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    def get_plugin(self, plugin_id: str) -> dict[str, Any]:
        r = self._client.get(f"/api/v1/plugins/{plugin_id}")
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    def connect(
        self,
        plugin_id: str,
        session_token: str,
        packaging: str = "local_script",
        label: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {session_token}"}
        body: dict[str, Any] = {"packaging": packaging}
        if label:
            body["label"] = label
        r = self._client.post(
            f"/api/v1/plugins/{plugin_id}/connect",
            headers=headers,
            json=body,
        )
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    def me(self) -> dict[str, Any]:
        r = self._client.get("/api/v1/plugin/me", headers=self._plugin_headers())
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    def download_url(self, file_id: str) -> dict[str, Any]:
        r = self._client.post(
            f"/api/v1/plugin/files/{file_id}/download-url",
            headers=self._plugin_headers(),
        )
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    def upload_url(
        self, filename: str, parent_folder: str | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"filename": filename}
        if parent_folder:
            body["parent_folder"] = parent_folder
        r = self._client.post(
            "/api/v1/plugin/files/upload-url",
            headers=self._plugin_headers(),
            json=body,
        )
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    def complete_upload(
        self,
        completion_token: str,
        provider_file_id: str,
        filename: str,
        size: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "completion_token": completion_token,
            "provider_file_id": provider_file_id,
            "filename": filename,
        }
        if size is not None:
            body["size"] = size
        r = self._client.post(
            "/api/v1/plugin/files/complete",
            headers=self._plugin_headers(),
            json=body,
        )
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    def close(self) -> None:
        self._client.close()
