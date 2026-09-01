"""Semptify-PI real Core — FastAPI plugin API with OAuth, tokens, and containment."""
from __future__ import annotations

import json
import secrets
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.capabilities import download_capability, is_contained, upload_capability
from core.config import CoreConfig
from core.database import Database
from core.models import Base, PluginManifest, VaultFile
from core.models import PluginToken as PluginTokenModel
from core.seeding import seed_manifests
from core.tokens import TokenManager


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat().replace("+", "+")


class CoreState:
    """Shared application state."""

    def __init__(self, database: Database | None = None) -> None:
        self.db = database or Database()
        self.tokens = TokenManager()
        self.config = CoreConfig.from_env()


state = CoreState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create tables and seed manifests on startup (simple, not a migration tool)."""
    async with state.db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with state.db.session() as session:
        async with session.begin():
            await seed_manifests(session)
            await session.commit()
    yield
    await state.db.engine.dispose()


app = FastAPI(
    title="Semptify-PI Core",
    description="Real Core for the Semptify Plugin Interface.",
    version="2.0.0",
    lifespan=lifespan,
)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with state.db.session() as session:
        yield session


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


class PluginTokenView(BaseModel):
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


class DirectRequest(BaseModel):
    endpoint: str
    method: str
    headers: dict[str, str]
    query: Optional[dict[str, Any]] = None
    body: Optional[dict] = None


class DirectUrlResponse(BaseModel):
    download_url: Optional[str] = None
    direct_request: Optional[DirectRequest] = None
    expires_at: str


class UploadRequest(BaseModel):
    filename: str
    parent_folder: Optional[str] = None


class UploadUrlResponse(BaseModel):
    upload_url: Optional[str] = None
    direct_request: Optional[DirectRequest] = None
    completion_token: str
    expires_at: str


class CompleteUploadRequest(BaseModel):
    completion_token: str
    provider_file_id: str
    filename: str
    size: Optional[int] = None
    vault_path: Optional[str] = None


class VaultFileView(BaseModel):
    file_id: str
    filename: str
    provider_file_id: str
    vault_path: str
    size: Optional[int]
    recorded_at: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


async def require_session(
    authorization: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> str:
    """Validate the tenant session token and return the tenant id."""
    if not authorization or not authorization.credentials:
        raise HTTPException(status_code=401, detail="Missing session token")
    # Phase 2: a real session token would be validated against Core's session store.
    # For now, the session token IS the tenant id when it starts with a synthetic prefix.
    cred = authorization.credentials
    if not cred.startswith("sess_"):
        raise HTTPException(status_code=401, detail="Invalid session token")
    return cred


async def require_plugin_token(
    authorization: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> PluginTokenModel:
    if not authorization or not authorization.credentials:
        raise HTTPException(status_code=401, detail="Missing plugin token")
    token = await state.tokens.validate(session, authorization.credentials)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid or revoked plugin token")
    return token


async def _get_manifest(session: AsyncSession, plugin_id: str) -> PluginManifest:
    stmt = select(PluginManifest).where(
        PluginManifest.plugin_id == plugin_id,
        PluginManifest.status == "approved",
    )
    result = await session.execute(stmt)
    manifest = result.scalar_one_or_none()
    if not manifest:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return manifest


@app.get("/api/v1/plugins")
async def list_plugins(
    packaging: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(PluginManifest).where(PluginManifest.status == "approved")
    result = await session.execute(stmt)
    manifests = result.scalars().all()
    items = []
    for m in manifests:
        if packaging and packaging not in json.loads(m.packaging):
            continue
        items.append(_manifest_to_dict(m))
    return {"plugins": items}


@app.get("/api/v1/plugins/{plugin_id}")
async def get_plugin(plugin_id: str, session: AsyncSession = Depends(get_session)):
    manifest = await _get_manifest(session, plugin_id)
    return _manifest_to_dict(manifest)


@app.get("/api/v1/plugins/tokens")
async def list_tokens(
    user_id: str = Depends(require_session),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(PluginTokenModel).where(PluginTokenModel.tenant_id == user_id)
    result = await session.execute(stmt)
    tokens = result.scalars().all()
    return {"tokens": [_token_to_view(t).model_dump() for t in tokens]}


@app.delete("/api/v1/plugins/tokens/{token_id}", status_code=204)
async def revoke_token(
    token_id: str,
    user_id: str = Depends(require_session),
    session: AsyncSession = Depends(get_session),
):
    ok = await state.tokens.revoke(session, token_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Token not found")
    await session.commit()
    return None


@app.post("/api/v1/plugins/{plugin_id}/connect")
async def connect_plugin(
    plugin_id: str,
    body: ConnectRequest,
    user_id: str = Depends(require_session),
    session: AsyncSession = Depends(get_session),
):
    manifest = await _get_manifest(session, plugin_id)
    if body.packaging not in json.loads(manifest.packaging):
        raise HTTPException(
            status_code=400,
            detail=f"Packaging '{body.packaging}' not offered by this plugin",
        )

    raw, token = await state.tokens.issue(
        session,
        plugin_id=plugin_id,
        tenant_id=user_id,
        packaging=body.packaging,
        scopes=json.loads(manifest.required_scopes),
        label=body.label,
    )
    await session.commit()
    return TokenIssueResponse(
        token=raw,
        token_id=token.id,
        plugin_id=plugin_id,
        scopes=json.loads(token.scopes),
        packaging=body.packaging,
        expires_at=iso(token.expires_at),
    )


@app.get("/api/v1/plugin/me")
async def get_me(
    token: PluginTokenModel = Depends(require_plugin_token),
):
    return PluginContext(
        user_id=token.tenant_id,
        plugin_id=token.plugin_id,
        packaging=token.packaging,
        effective_scopes=json.loads(token.scopes),
        expires_at=iso(token.expires_at),
    )


@app.post(
    "/api/v1/plugin/files/{file_id}/download-url",
    response_model=DirectUrlResponse,
    response_model_exclude_none=True,
)
async def get_download_url(
    file_id: str,
    provider: str = Query(default="google_drive", pattern="^(google_drive|dropbox|onedrive)$"),
    token: PluginTokenModel = Depends(require_plugin_token),
    session: AsyncSession = Depends(get_session),
):
    if not await _has_scope(token, ["vault:read", "documents:capability"]):
        raise HTTPException(status_code=403, detail="Scope required")

    if not await state.tokens.can_access_file(session, token, file_id):
        raise HTTPException(status_code=403, detail="File not found for this tenant")

    cap = download_capability(provider, file_id)
    return DirectUrlResponse(
        download_url=cap.get("download_url"),
        direct_request=cap.get("direct_request"),
        expires_at=cap["expires_at"],
    )


@app.post(
    "/api/v1/plugin/files/upload-url",
    response_model=UploadUrlResponse,
    response_model_exclude_none=True,
)
async def get_upload_url(
    body: UploadRequest,
    provider: str = Query(default="google_drive", pattern="^(google_drive|dropbox|onedrive)$"),
    token: PluginTokenModel = Depends(require_plugin_token),
    session: AsyncSession = Depends(get_session),
):
    if not await _has_scope(token, ["vault:write", "documents:capability"]):
        raise HTTPException(status_code=403, detail="Scope required")

    try:
        cap = upload_capability(provider, body.filename, body.parent_folder)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UploadUrlResponse(
        upload_url=cap.get("upload_url"),
        direct_request=cap.get("direct_request"),
        completion_token=cap["completion_token"],
        expires_at=cap["expires_at"],
    )


@app.post("/api/v1/plugin/files/complete")
async def complete_upload(
    body: CompleteUploadRequest,
    token: PluginTokenModel = Depends(require_plugin_token),
    session: AsyncSession = Depends(get_session),
):
    if not await _has_scope(token, ["vault:write"]):
        raise HTTPException(status_code=403, detail="Scope required")

    vault_path = body.vault_path or f"{state.config.vault_folder.rstrip('/')}/{body.filename}"
    if not is_contained(vault_path):
        raise HTTPException(status_code=400, detail="Vault path escapes containment folder")

    file_id = "f_" + secrets.token_urlsafe(8)[:12]
    recorded = utc_now()
    vf = VaultFile(
        file_id=file_id,
        tenant_id=token.tenant_id,
        provider="unknown",
        provider_file_id=body.provider_file_id,
        filename=body.filename,
        vault_path=vault_path,
        size=body.size,
    )
    session.add(vf)
    await session.commit()
    return VaultFileView(
        file_id=file_id,
        filename=body.filename,
        provider_file_id=body.provider_file_id,
        vault_path=vault_path,
        size=body.size,
        recorded_at=iso(recorded),
    )


async def _has_scope(token: PluginTokenModel, scopes: list[str]) -> bool:
    token_scopes = set(json.loads(token.scopes))
    return any(s in token_scopes for s in scopes)


def _manifest_to_dict(m: PluginManifest) -> dict:
    return {
        "plugin_id": m.plugin_id,
        "name": m.name,
        "version": m.version,
        "description": m.description,
        "author": m.author,
        "license": m.license,
        "homepage_url": m.homepage_url,
        "packaging": json.loads(m.packaging),
        "required_scopes": json.loads(m.required_scopes),
        "optional_scopes": json.loads(m.optional_scopes),
        "api_version": m.api_version,
        "downloads": json.loads(m.downloads),
        "connect": json.loads(m.connect) if m.connect else None,
        "icon_url": m.icon_url,
        "status": m.status,
    }


def _token_to_view(t: PluginTokenModel) -> PluginTokenView:
    return PluginTokenView(
        token_id=t.id,
        plugin_id=t.plugin_id,
        label=t.label,
        scopes=json.loads(t.scopes),
        packaging=t.packaging,
        created_at=iso(t.created_at),
        last_used_at=iso(t.last_used_at) if t.last_used_at else None,
        expires_at=iso(t.expires_at),
        revoked=t.is_revoked,
    )


def run() -> None:
    import uvicorn
    uvicorn.run("core.main:app", host="127.0.0.1", port=9000, reload=False)


if __name__ == "__main__":
    run()
