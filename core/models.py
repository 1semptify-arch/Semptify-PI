"""SQLAlchemy models for the Semptify-PI real Core."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """DateTime stored as naive but returned as timezone-aware UTC."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PluginManifest(Base):
    """Canonical plugin manifest registry (minimal Phase 2)."""

    __tablename__ = "plugin_manifests"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    plugin_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(128), nullable=False)
    license: Mapped[str] = mapped_column(String(32), nullable=False)
    homepage_url: Mapped[str] = mapped_column(String(256), nullable=False)
    packaging: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    required_scopes: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    optional_scopes: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    api_version: Mapped[str] = mapped_column(String(8), nullable=False)
    downloads: Mapped[str] = mapped_column(Text, nullable=False)  # JSON dict
    connect: Mapped[str] = mapped_column(Text, nullable=True)  # JSON dict
    icon_url: Mapped[str] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="approved")


class PluginToken(Base):
    """A Semptify-issued plugin token for a specific plugin + tenant."""

    __tablename__ = "plugin_tokens"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: uuid4().hex[:16]
    )
    # SHA-256 hash of the raw token. The raw token itself is never stored.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    plugin_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    packaging: Mapped[str] = mapped_column(String(32), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        return utc_now() > self.expires_at


class ProviderToken(Base):
    """Encrypted provider refresh/access tokens for a tenant."""

    __tablename__ = "provider_tokens"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: uuid4().hex[:16]
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(16), nullable=False)
    # Refresh token is encrypted at rest by the core before storage.
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)


class VaultFile(Base):
    """A record of a file the tenant has created or imported via Semptify."""

    __tablename__ = "vault_files"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: uuid4().hex[:16]
    )
    file_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(16), nullable=False)
    provider_file_id: Mapped[str] = mapped_column(String(128), nullable=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    vault_path: Mapped[str] = mapped_column(String(512), nullable=False)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
