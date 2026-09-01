"""Provider capability generation and vault-path containment checks."""
from __future__ import annotations

import posixpath
import secrets
from datetime import datetime, timedelta, timezone

from core.config import CoreConfig


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


VAULT_FOLDER: str = CoreConfig.from_env().vault_folder


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


def _provider_token() -> str:
    return "prv_" + secrets.token_urlsafe(32)


def _expires_at() -> datetime:
    return utc_now() + timedelta(hours=4)


def _google_drive_download(file_id: str) -> dict:
    return {
        "direct_request": {
            "endpoint": f"https://www.googleapis.com/drive/v3/files/{file_id}",
            "method": "GET",
            "headers": {"Authorization": f"Bearer {_provider_token()}"},
            "query": {"alt": "media"},
        },
        "expires_at": _expires_at().isoformat(),
    }


def _google_drive_upload(filename: str, parent_folder: str | None = None) -> dict:
    vault_path = make_vault_path(filename, parent_folder)
    return {
        "direct_request": {
            "endpoint": "https://www.googleapis.com/upload/drive/v3/files",
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {_provider_token()}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            "query": {"uploadType": "resumable"},
            "body": {"name": filename, "parents": [vault_path.rsplit("/", 1)[0]]},
        },
        "completion_token": "cpl_" + secrets.token_urlsafe(12)[:16],
        "expires_at": _expires_at().isoformat(),
    }


def _dropbox_download(file_id: str) -> dict:
    return {
        "download_url": (
            f"https://dl.dropboxusercontent.com/apitl/1/{file_id}"
            f"?token={secrets.token_urlsafe(16)}"
        ),
        "expires_at": _expires_at().isoformat(),
    }


def _dropbox_upload(filename: str, parent_folder: str | None = None) -> dict:
    vault_path = make_vault_path(filename, parent_folder)
    return {
        "direct_request": {
            "endpoint": "https://content.dropboxapi.com/2/files/upload",
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {_provider_token()}",
                "Content-Type": "application/octet-stream",
                "Dropbox-API-Arg": (
                    f'{{"path": "{vault_path}", "mode": "add", "autorename": true}}'
                ),
            },
        },
        "completion_token": "cpl_" + secrets.token_urlsafe(12)[:16],
        "expires_at": _expires_at().isoformat(),
    }


def _onedrive_download(file_id: str) -> dict:
    return {
        "download_url": (
            f"https://public-sn3302.files.1drv.com/y2pcT7OaUEExF7EHOlpTjCE55mIUoiX7H3sx1ff6I-nP35XUTBqZlnkh9FJhWb_pf9sZ7LEpEchvDznIbQig0hWBeidpwFkOqSKCwQylisarN6T0ecAeMvantizBUzM2PA1/{file_id}"
        ),
        "expires_at": _expires_at().isoformat(),
    }


def _onedrive_upload(filename: str, parent_folder: str | None = None) -> dict:
    vault_path = make_vault_path(filename, parent_folder)
    completion = "cpl_" + secrets.token_urlsafe(12)[:16]
    return {
        "upload_url": f"https://sn3302.up.1drv.com/up/{completion}",
        "completion_token": completion,
        "vault_path": vault_path,
        "expires_at": _expires_at().isoformat(),
    }


def download_capability(provider: str, file_id: str) -> dict:
    """Return a provider-specific download capability response."""
    if provider == "dropbox":
        return _dropbox_download(file_id)
    if provider == "onedrive":
        return _onedrive_download(file_id)
    if provider == "google_drive":
        return _google_drive_download(file_id)
    raise ValueError(f"unsupported provider: {provider}")


def upload_capability(provider: str, filename: str, parent_folder: str | None = None) -> dict:
    """Return a provider-specific upload capability response."""
    if provider == "dropbox":
        return _dropbox_upload(filename, parent_folder)
    if provider == "onedrive":
        return _onedrive_upload(filename, parent_folder)
    if provider == "google_drive":
        return _google_drive_upload(filename, parent_folder)
    raise ValueError(f"unsupported provider: {provider}")
