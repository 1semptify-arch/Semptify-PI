"""Semptify-PI mock Core — FastAPI test double for plugin API validation.

This is a standalone test double. It does not import from Semptify Core, does not
use real tenant data, and does not transmit document bytes. All tokens, users,
and cloud-provider URLs are synthetic.

Run with:
    uvicorn mock_core.main:app --port 9000
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat().replace("+", "+")


# ---------------------------------------------------------------------------
# Data stores (in-memory, synthetic)
# ---------------------------------------------------------------------------

MANIFESTS: dict[str, dict] = {
    "example-document-organizer": {
        "plugin_id": "example-document-organizer",
        "name": "Document Organizer",
        "version": "1.0.0",
        "description": "Sorts and labels documents in your Semptify vault.",
        "author": "Semptify",
        "license": "AGPL-3.0",
        "homepage_url": "https://semptify.org/plugins/example-document-organizer",
        "packaging": ["local_script"],
        "required_scopes": ["vault:read", "vault:write", "documents:capability"],
        "optional_scopes": ["context:read"],
        "api_version": "v1",
        "downloads": {
            "local_script": {
                "download_url": "https://github.com/1semptify-arch/Semptify-PI/releases/download/v0.1.0/example-document-organizer.py",
                "python": "https://github.com/1semptify-arch/Semptify-PI/releases/download/v0.1.0/example-document-organizer.py",
            }
        },
        "connect": {
            "local_script_config_template": '{"core_url": "https://plugins.semptify.org", "plugin_token": "<PASTE TOKEN HERE>"}'
        },
        "icon_url": "https://semptify.org/static/icons/example-document-organizer.svg",
        "status": "approved",
    },
    "case-packet-builder": {
        "plugin_id": "case-packet-builder",
        "name": "Case Packet Builder",
        "version": "0.5.0",
        "description": "Builds court-ready packets from your timeline and documents.",
        "author": "Semptify",
        "license": "AGPL-3.0",
        "homepage_url": "https://semptify.org/plugins/case-packet-builder",
        "packaging": ["local_script", "desktop_app"],
        "required_scopes": ["vault:read", "vault:write", "documents:capability"],
        "api_version": "v1",
        "downloads": {
            "local_script": {
                "download_url": "https://github.com/1semptify-arch/Semptify-PI/releases/download/v0.1.0/case-packet-builder.py",
            },
            "desktop_app": {
                "download_url": "https://github.com/1semptify-arch/Semptify-PI/releases/download/v0.1.0/case-packet-builder.exe",
                "windows": "https://github.com/1semptify-arch/Semptify-PI/releases/download/v0.1.0/case-packet-builder.exe",
            },
        },
        "connect": {
            "desktop_redirect_scheme": "semptify-plugin://",
            "local_script_config_template": '{"core_url": "https://plugins.semptify.org", "plugin_token": "<PASTE TOKEN HERE>"}'
        },
        "status": "approved",
    },
}

# plugin token store: keyed by raw token string for mock simplicity
tokens_by_raw: dict[str, dict] = {}
tokens_by_id: dict[str, dict] = {}
# pairing code -> token_id
pairing_codes: dict[str, str] = {}

SYNTHETIC_USER = "gt7x9km2pq"

# ---------------------------------------------------------------------------
# Pydantic models (mirror the OpenAPI schemas)
# ---------------------------------------------------------------------------


class ConnectRequest(BaseModel):
    packaging: str = Field(..., pattern="^(browser_extension|desktop_app|local_script)$")
    label: Optional[str] = Field(None, max_length=128)


class TokenIssueResponse(BaseModel):
    token: str
    token_id: str
    plugin_id: str
    scopes: list[str]
    packaging: str
    expires_at: Optional[str]


class PluginToken(BaseModel):
    token_id: str
    plugin_id: str
    label: Optional[str]
    scopes: list[str]
    packaging: str
    created_at: str
    last_used_at: Optional[str]
    expires_at: Optional[str]
    revoked: bool


class PluginContext(BaseModel):
    user_id: str
    plugin_id: str
    packaging: str
    effective_scopes: list[str]
    expires_at: Optional[str]


class PairRequest(BaseModel):
    pairing_code: str = Field(..., pattern="^[A-Z0-9]{4}-[A-Z0-9]{4}$")
    plugin_id: str


class DirectUrlResponse(BaseModel):
    download_url: str
    expires_at: str


class UploadRequest(BaseModel):
    filename: str
    parent_folder: Optional[str] = None


class UploadUrlResponse(BaseModel):
    upload_url: str
    completion_token: str
    expires_at: str


class CompleteUploadRequest(BaseModel):
    completion_token: str
    provider_file_id: str
    filename: str
    size: Optional[int] = None


class VaultFile(BaseModel):
    file_id: str
    filename: str
    provider_file_id: str
    vault_path: str
    size: Optional[int]
    recorded_at: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

bearer_scheme = HTTPBearer(auto_error=False)


def _token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def require_session(
    authorization: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Mock tenant session check. Accepts any non-empty bearer string."""
    if not authorization or not authorization.credentials:
        raise HTTPException(status_code=401, detail="Missing session token")
    return SYNTHETIC_USER


def require_plugin_token(
    authorization: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if not authorization or not authorization.credentials:
        raise HTTPException(status_code=401, detail="Missing plugin token")
    raw = authorization.credentials
    token = tokens_by_raw.get(raw)
    if not token or token.get("revoked"):
        raise HTTPException(status_code=401, detail="Invalid or revoked plugin token")
    token["last_used_at"] = utc_now()
    return token


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Semptify-PI Mock Core",
    description="Standalone test double for the Semptify Plugin Interface API.",
    version="1.0.0",
)


@app.get("/api/v1/plugins")
def list_plugins(
    packaging: Optional[str] = Query(default=None),
):
    """List approved plugins. Public or tenant-scoped."""
    result = []
    for manifest in MANIFESTS.values():
        if manifest.get("status") != "approved":
            continue
        if packaging and packaging not in manifest.get("packaging", []):
            continue
        result.append(manifest)
    return {"plugins": result}


@app.get("/api/v1/plugins/tokens")
def list_tokens(user_id: str = Depends(require_session)):
    """List active plugin tokens for the tenant."""
    result = []
    for token in tokens_by_id.values():
        if token["user_id"] != user_id:
            continue
        result.append(
            PluginToken(
                token_id=token["token_id"],
                plugin_id=token["plugin_id"],
                label=token.get("label"),
                scopes=token["scopes"],
                packaging=token["packaging"],
                created_at=iso(token["created_at"]),
                last_used_at=iso(token["last_used_at"]) if token["last_used_at"] else None,
                expires_at=iso(token["expires_at"]) if token["expires_at"] else None,
                revoked=token["revoked"],
            )
        )
    return {"tokens": result}


@app.delete("/api/v1/plugins/tokens/{token_id}", status_code=204)
def revoke_token(token_id: str, user_id: str = Depends(require_session)):
    token = tokens_by_id.get(token_id)
    if not token or token["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Token not found")
    token["revoked"] = True
    return None


@app.post("/api/v1/plugins/pair")
def pair_token(body: PairRequest):
    """Exchange a short pairing code for the real plugin token."""
    token_id = pairing_codes.get(body.pairing_code)
    if not token_id:
        raise HTTPException(status_code=404, detail="Pairing code not found")
    token = tokens_by_id.get(token_id)
    if not token or token.get("revoked"):
        raise HTTPException(status_code=404, detail="Token no longer valid")
    if token["plugin_id"] != body.plugin_id:
        raise HTTPException(status_code=400, detail="Plugin mismatch")

    return TokenIssueResponse(
        token=token["raw"],
        token_id=token["token_id"],
        plugin_id=token["plugin_id"],
        scopes=token["scopes"],
        packaging=token["packaging"],
        expires_at=iso(token["expires_at"]) if token["expires_at"] else None,
    )


@app.get("/api/v1/plugins/{plugin_id}")
def get_plugin(plugin_id: str):
    manifest = MANIFESTS.get(plugin_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return manifest


@app.post("/api/v1/plugins/{plugin_id}/connect")
def connect_plugin(
    plugin_id: str,
    body: ConnectRequest,
    user_id: str = Depends(require_session),
):
    """Issue a scoped plugin token. Returns raw token once."""
    manifest = MANIFESTS.get(plugin_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Plugin not found")
    if body.packaging not in manifest.get("packaging", []):
        raise HTTPException(
            status_code=400,
            detail=f"Packaging '{body.packaging}' not offered by this plugin",
        )

    raw = "pl_" + secrets.token_urlsafe(32)
    token_id = "tok_" + secrets.token_urlsafe(8)[:12]
    scopes = manifest["required_scopes"]
    expires = utc_now() + timedelta(days=365)

    token = {
        "raw": raw,
        "token_id": token_id,
        "plugin_id": plugin_id,
        "user_id": user_id,
        "scopes": scopes,
        "packaging": body.packaging,
        "label": body.label,
        "created_at": utc_now(),
        "last_used_at": None,
        "expires_at": expires,
        "revoked": False,
    }
    tokens_by_raw[raw] = token
    tokens_by_id[token_id] = token

    # generate a pairing code for desktop/script clients
    code = f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}"
    pairing_codes[code] = token_id

    return TokenIssueResponse(
        token=raw,
        token_id=token_id,
        plugin_id=plugin_id,
        scopes=scopes,
        packaging=body.packaging,
        expires_at=iso(expires),
    )


@app.get("/api/v1/plugin/me")
def get_me(token: dict = Depends(require_plugin_token)):
    """Return the current plugin context and effective scopes."""
    return PluginContext(
        user_id=token["user_id"],
        plugin_id=token["plugin_id"],
        packaging=token["packaging"],
        effective_scopes=token["scopes"],
        expires_at=iso(token["expires_at"]) if token["expires_at"] else None,
    )


@app.post("/api/v1/plugin/files/{file_id}/download-url")
def get_download_url(file_id: str, token: dict = Depends(require_plugin_token)):
    """Return a fake, short-lived direct download URL."""
    if "vault:read" not in token["scopes"] and "documents:capability" not in token["scopes"]:
        raise HTTPException(status_code=403, detail="Scope required")

    expires = utc_now() + timedelta(hours=4)
    return DirectUrlResponse(
        download_url=f"https://example-provider.invalid/download/{file_id}?token={secrets.token_urlsafe(16)}",
        expires_at=iso(expires),
    )


@app.post("/api/v1/plugin/files/upload-url")
def get_upload_url(body: UploadRequest, token: dict = Depends(require_plugin_token)):
    """Return a fake, short-lived direct upload URL."""
    if "vault:write" not in token["scopes"] and "documents:capability" not in token["scopes"]:
        raise HTTPException(status_code=403, detail="Scope required")

    expires = utc_now() + timedelta(hours=4)
    completion = "cpl_" + secrets.token_urlsafe(12)[:16]
    return UploadUrlResponse(
        upload_url=f"https://example-provider.invalid/upload/{completion}?token={secrets.token_urlsafe(16)}",
        completion_token=completion,
        expires_at=iso(expires),
    )


@app.post("/api/v1/plugin/files/complete")
def complete_upload(body: CompleteUploadRequest, token: dict = Depends(require_plugin_token)):
    """Record a completed direct upload (metadata only, no bytes)."""
    if "vault:write" not in token["scopes"]:
        raise HTTPException(status_code=403, detail="Scope required")

    file_id = "f_" + secrets.token_urlsafe(8)[:12]
    recorded = utc_now()
    vault_path = "/Semptify5.0/Inbox/" + body.filename

    return VaultFile(
        file_id=file_id,
        filename=body.filename,
        provider_file_id=body.provider_file_id,
        vault_path=vault_path,
        size=body.size,
        recorded_at=iso(recorded),
    )


# ---------------------------------------------------------------------------
# Console entrypoint
# ---------------------------------------------------------------------------

def run():
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9000)


if __name__ == "__main__":
    run()
