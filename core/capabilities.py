"""Provider capability generation and vault-path containment checks."""
from __future__ import annotations

import json
import posixpath
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import oauth as oauth_module
from core.config import CoreConfig
from core.models import ProviderToken, VaultFile


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


VAULT_FOLDER: str = CoreConfig.from_env().vault_folder


# Module-level OAuth manager. Callers and tests can override by monkeypatching
# this object; see core/main.py for production use.
oauth = oauth_module.OAuthManager()


def _sanitize_filename(filename: str) -> str:
    """Remove path components that could escape the vault."""
    # Reject absolute or parent-reference paths outright.
    if filename.startswith("/") or ".." in filename.split("/"):
        raise ValueError(f"filename contains path traversal: {filename!r}")

    # Collapse any . or .. and strip leading / that would make the path absolute.
    cleaned = posixpath.normpath(filename)
    if cleaned.startswith("/"):
        cleaned = cleaned.lstrip("/")
    # Remove any leading ../ left by normpath when the input was already relative.
    parts = cleaned.split("/")
    safe = [p for p in parts if p and p != ".." and p != "."]
    return "/".join(safe)


def make_vault_path(filename: str, parent_folder: str | None = None) -> str:
    """Return a contained vault path or raise ValueError if it escapes."""
    parent = (parent_folder or VAULT_FOLDER).rstrip("/")
    base = _sanitize_filename(filename)
    if not base:
        raise ValueError("filename is empty after sanitization")

    # Join parent with sanitized base. If the base tried to escape, it will
    # be relative and still inside parent. We then verify it does not step
    # above parent.
    full = posixpath.join(parent, base)
    if not full.startswith(parent + "/") and full != parent:
        raise ValueError(f"path escapes parent folder: {full}")

    return full


def is_contained(vault_path: str) -> bool:
    """Check whether an existing vault path is inside the configured folder."""
    normalized = posixpath.normpath(vault_path)
    return normalized == VAULT_FOLDER or normalized.startswith(VAULT_FOLDER + "/")


def _completion_token() -> str:
    return "cpl_" + secrets.token_urlsafe(12)[:16]


def _expires_at(token_response: dict[str, Any]) -> datetime:
    """Derive an expiry time from a provider token response."""
    expires_in = token_response.get("expires_in")
    try:
        if isinstance(expires_in, (int, float)):
            return utc_now() + timedelta(seconds=int(expires_in))
        if isinstance(expires_in, str):
            return utc_now() + timedelta(seconds=int(expires_in))
    except (TypeError, ValueError):
        pass
    return utc_now() + timedelta(hours=1)


async def _provider_token(tenant_id: str, provider: str, session: AsyncSession) -> ProviderToken:
    stmt = select(ProviderToken).where(
        ProviderToken.tenant_id == tenant_id,
        ProviderToken.provider == provider,
    )
    result = await session.execute(stmt)
    token = result.scalar_one_or_none()
    if token is None:
        raise ValueError(f"provider not connected for tenant: {provider}")
    return token


async def _access_token(
    provider: str,
    tenant_id: str,
    session: AsyncSession,
) -> tuple[str, datetime]:
    """Return a live access token and its expiry for the tenant/provider."""
    token = await _provider_token(tenant_id, provider, session)
    refresh = oauth.crypto.decrypt(token.refresh_token_encrypted)
    response = await oauth.refresh_access_token(provider, refresh)
    access_token = response.get("access_token")
    if not access_token or not isinstance(access_token, str):
        raise ValueError("provider did not return an access token")
    return access_token, _expires_at(response)


async def _vault_file(file_id: str, tenant_id: str, session: AsyncSession) -> VaultFile:
    stmt = select(VaultFile).where(
        VaultFile.file_id == file_id,
        VaultFile.tenant_id == tenant_id,
    )
    result = await session.execute(stmt)
    file = result.scalar_one_or_none()
    if file is None:
        raise ValueError("file not found for tenant")
    return file


# ---------------------------------------------------------------------------
# Google Drive helpers
# ---------------------------------------------------------------------------


_GDRIVE_FOLDER_MIME = "application/vnd.google-apps.folder"


async def _google_drive_find_child(
    access_token: str,
    parent_id: str,
    name: str,
) -> str | None:
    """Return the ID of a child folder, or None if not found."""
    query = (
        f"trashed=false and mimeType='{_GDRIVE_FOLDER_MIME}' "
        f"and name='{name}' and '{parent_id}' in parents"
    )
    url = "https://www.googleapis.com/drive/v3/files"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"q": query, "fields": "files(id)", "pageSize": "1"},
        )
        response.raise_for_status()
        data = cast(dict[str, Any], response.json())
        files = cast(list[dict[str, Any]], data.get("files", []))
        if files:
            return cast(str | None, files[0].get("id"))
    return None


async def _google_drive_create_folder(
    access_token: str,
    parent_id: str,
    name: str,
) -> str:
    """Create a folder under parent_id and return its ID."""
    url = "https://www.googleapis.com/drive/v3/files"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "name": name,
                "mimeType": _GDRIVE_FOLDER_MIME,
                "parents": [parent_id],
            },
        )
        response.raise_for_status()
        data = cast(dict[str, Any], response.json())
        folder_id = cast(str, data.get("id"))
        if not folder_id:
            raise ValueError("Google Drive did not return a folder id")
        return folder_id


async def _google_drive_ensure_folder(
    access_token: str,
    folder_path: str,
) -> str:
    """Find or create the folder path, return the final folder ID.

    The path is relative to the user's Google Drive root (e.g.
    "Semptify5.0/Inbox"). Missing segments are created.
    """
    parts = [p for p in folder_path.strip("/").split("/") if p]
    parent_id = "root"
    for name in parts:
        child_id = await _google_drive_find_child(access_token, parent_id, name)
        if child_id is None:
            child_id = await _google_drive_create_folder(access_token, parent_id, name)
        parent_id = child_id
    return parent_id


async def _google_drive_download(
    access_token: str,
    expires_at: datetime,
    provider_file_id: str,
) -> dict[str, Any]:
    return {
        "direct_request": {
            "endpoint": f"https://www.googleapis.com/drive/v3/files/{provider_file_id}",
            "method": "GET",
            "headers": {"Authorization": f"Bearer {access_token}"},
            "query": {"alt": "media"},
        },
        "expires_at": expires_at.isoformat(),
    }


async def _google_drive_upload(
    access_token: str,
    expires_at: datetime,
    filename: str,
    vault_path: str,
) -> dict[str, Any]:
    parent_folder = vault_path.rsplit("/", 1)[0]
    folder_id = await _google_drive_ensure_folder(access_token, parent_folder)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.googleapis.com/upload/drive/v3/files",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": "application/octet-stream",
            },
            params={"uploadType": "resumable"},
            json={"name": filename, "parents": [folder_id]},
        )
        response.raise_for_status()
        location = response.headers.get("location")
        if not location:
            raise ValueError("Google Drive did not return an upload location")

    return {
        "direct_request": {
            "endpoint": location,
            "method": "PUT",
            "headers": {"Content-Type": "application/octet-stream"},
        },
        "completion_token": _completion_token(),
        "vault_path": vault_path,
        "expires_at": expires_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Dropbox helpers
# ---------------------------------------------------------------------------


async def _dropbox_download(
    access_token: str,
    expires_at: datetime,
    provider_file_id: str,
) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.dropboxapi.com/2/files/get_temporary_link",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"path": provider_file_id},
        )
        response.raise_for_status()
        data = response.json()
        link = data.get("link")
        if not link:
            raise ValueError("Dropbox did not return a temporary link")

    return {"download_url": link, "expires_at": expires_at.isoformat()}


async def _dropbox_upload(
    access_token: str,
    expires_at: datetime,
    vault_path: str,
) -> dict[str, Any]:
    return {
        "direct_request": {
            "endpoint": "https://content.dropboxapi.com/2/files/upload",
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/octet-stream",
                "Dropbox-API-Arg": json.dumps(
                    {"path": vault_path, "mode": "add", "autorename": True}
                ),
            },
        },
        "completion_token": _completion_token(),
        "vault_path": vault_path,
        "expires_at": expires_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# OneDrive helpers
# ---------------------------------------------------------------------------


async def _onedrive_download(
    access_token: str,
    expires_at: datetime,
    provider_file_id: str,
) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://graph.microsoft.com/v1.0/me/drive/items/{provider_file_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()
        link = data.get("@microsoft.graph.downloadUrl")
        if not link:
            raise ValueError("OneDrive did not return a download URL")

    return {"download_url": link, "expires_at": expires_at.isoformat()}


async def _onedrive_upload(
    access_token: str,
    expires_at: datetime,
    vault_path: str,
) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.microsoft.com/v1.0/me/drive/root:{vault_path}:/createUploadSession",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()
        upload_url = data.get("uploadUrl")
        if not upload_url:
            raise ValueError("OneDrive did not return an upload URL")

    return {
        "upload_url": upload_url,
        "completion_token": _completion_token(),
        "vault_path": vault_path,
        "expires_at": expires_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def download_capability(
    provider: str,
    file_id: str,
    tenant_id: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """Return a provider-specific download capability response."""
    if provider not in {"google_drive", "dropbox", "onedrive"}:
        raise ValueError(f"unsupported provider: {provider}")

    vault_file = await _vault_file(file_id, tenant_id, session)
    access_token, expires_at = await _access_token(provider, tenant_id, session)

    if provider == "google_drive":
        return await _google_drive_download(access_token, expires_at, vault_file.provider_file_id)
    if provider == "dropbox":
        return await _dropbox_download(access_token, expires_at, vault_file.provider_file_id)
    return await _onedrive_download(access_token, expires_at, vault_file.provider_file_id)


async def upload_capability(
    provider: str,
    filename: str,
    parent_folder: str | None,
    tenant_id: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """Return a provider-specific upload capability response."""
    if provider not in {"google_drive", "dropbox", "onedrive"}:
        raise ValueError(f"unsupported provider: {provider}")

    vault_path = make_vault_path(filename, parent_folder)
    if not is_contained(vault_path):
        raise ValueError(f"path escapes vault: {vault_path}")

    access_token, expires_at = await _access_token(provider, tenant_id, session)

    if provider == "google_drive":
        return await _google_drive_upload(access_token, expires_at, filename, vault_path)
    if provider == "dropbox":
        return await _dropbox_upload(access_token, expires_at, vault_path)
    return await _onedrive_upload(access_token, expires_at, vault_path)
