"""Configuration for the Semptify-PI real Core.

Real provider credentials are never committed. They are read from environment
variables and are expected to be supplied at deploy time (Phase 5) or from
local `.env` during Brad's manual Phase 3 registration.
"""
from __future__ import annotations

import os
from datetime import timedelta


class CoreConfig:
    """Runtime configuration."""

    # ------------------------------------------------------------------
    # Service
    # ------------------------------------------------------------------
    core_url: str = os.getenv("SEMPIFY_PI_CORE_URL", "http://127.0.0.1:9000")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://semptify_pi:semptify_pi@localhost:5432/semptify_pi",
    )

    # ------------------------------------------------------------------
    # Token lifetimes
    # ------------------------------------------------------------------
    plugin_token_lifetime: timedelta = timedelta(
        days=int(os.getenv("SEMPIFY_PI_PLUGIN_TOKEN_DAYS", "90"))
    )
    provider_access_token_lifetime: timedelta = timedelta(
        minutes=int(os.getenv("SEMPIFY_PI_PROVIDER_TOKEN_MINUTES", "30"))
    )

    # ------------------------------------------------------------------
    # Containment
    # ------------------------------------------------------------------
    # Every provider writes into this vault folder. Relative paths are
    # normalized and rejected if they escape it.
    vault_folder: str = os.getenv("SEMPIFY_PI_VAULT_FOLDER", "/Semptify5.0/Inbox")

    # ------------------------------------------------------------------
    # Provider OAuth (Phase 3 credentials)
    # ------------------------------------------------------------------
    google_client_id: str = os.getenv("SEMPIFY_PI_GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("SEMPIFY_PI_GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv(
        "SEMPIFY_PI_GOOGLE_REDIRECT_URI", "http://127.0.0.1:9000/auth/google/callback"
    )

    dropbox_client_id: str = os.getenv("SEMPIFY_PI_DROPBOX_CLIENT_ID", "")
    dropbox_client_secret: str = os.getenv("SEMPIFY_PI_DROPBOX_CLIENT_SECRET", "")
    dropbox_redirect_uri: str = os.getenv(
        "SEMPIFY_PI_DROPBOX_REDIRECT_URI", "http://127.0.0.1:9000/auth/dropbox/callback"
    )

    onedrive_client_id: str = os.getenv("SEMPIFY_PI_ONEDRIVE_CLIENT_ID", "")
    onedrive_client_secret: str = os.getenv("SEMPIFY_PI_ONEDRIVE_CLIENT_SECRET", "")
    onedrive_redirect_uri: str = os.getenv(
        "SEMPIFY_PI_ONEDRIVE_REDIRECT_URI",
        "http://localhost:9000/auth/onedrive/callback",
    )

    @classmethod
    def from_env(cls) -> "CoreConfig":
        return cls()
