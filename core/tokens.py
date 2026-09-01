"""Plugin-token issuance, validation, and revocation."""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import CoreConfig
from core.models import PluginToken as PluginTokenModel
from core.models import VaultFile

PREFIX = "pl_"
TOKEN_BYTES = 32


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _generate_token() -> str:
    return PREFIX + secrets.token_urlsafe(TOKEN_BYTES)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TokenManager:
    """Issues, validates, and revokes plugin tokens."""

    def __init__(self, config: CoreConfig | None = None) -> None:
        self.config = config or CoreConfig.from_env()

    async def issue(
        self,
        session: AsyncSession,
        plugin_id: str,
        tenant_id: str,
        packaging: str,
        scopes: list[str],
        label: str | None = None,
    ) -> tuple[str, PluginTokenModel]:
        """Return the raw token (one-time) and the persisted model."""
        raw = _generate_token()
        token_hash = _hash(raw)

        expires = utc_now() + self.config.plugin_token_lifetime
        token = PluginTokenModel(
            token_hash=token_hash,
            plugin_id=plugin_id,
            tenant_id=tenant_id,
            packaging=packaging,
            scopes=json.dumps(scopes),
            label=label,
            expires_at=expires,
        )
        session.add(token)
        await session.flush()
        return raw, token

    async def validate(
        self, session: AsyncSession, raw: str
    ) -> PluginTokenModel | None:
        token_hash = _hash(raw)
        stmt = select(PluginTokenModel).where(
            PluginTokenModel.token_hash == token_hash
        )
        result = await session.execute(stmt)
        token = result.scalar_one_or_none()
        if token is None or token.is_revoked or token.is_expired:
            return None
        token.last_used_at = utc_now()
        await session.flush()
        return token

    async def revoke(self, session: AsyncSession, token_id: str, tenant_id: str) -> bool:
        stmt = select(PluginTokenModel).where(
            PluginTokenModel.id == token_id,
            PluginTokenModel.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        token = result.scalar_one_or_none()
        if token is None:
            return False
        if not token.is_revoked:
            token.revoked_at = utc_now()
            await session.flush()
        return True

    async def can_access_file(
        self, session: AsyncSession, token: PluginTokenModel, file_id: str
    ) -> bool:
        """Confirm the requested file belongs to the token's tenant."""
        stmt = select(VaultFile).where(
            VaultFile.file_id == file_id,
            VaultFile.tenant_id == token.tenant_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None
