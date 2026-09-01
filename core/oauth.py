"""OAuth flow helpers and provider token storage.

This module provides the start/callback URL builders and encrypted refresh-token
storage. It does not perform real HTTP calls in Phase 2; the actual code
exchange happens in Phase 3 once Brad has registered provider applications.
"""
from __future__ import annotations

import urllib.parse
from dataclasses import dataclass

from core.config import CoreConfig


@dataclass
class OAuthProviderConfig:
    name: str
    authorization_base: str
    token_url: str
    scopes: list[str]
    client_id: str
    client_secret: str
    redirect_uri: str


class OAuthManager:
    """Builds OAuth URLs and stores encrypted provider refresh tokens."""

    def __init__(self, config: CoreConfig | None = None) -> None:
        self.config = config or CoreConfig.from_env()

    def _provider_config(self, provider: str) -> OAuthProviderConfig:
        if provider == "google_drive":
            return OAuthProviderConfig(
                name="google_drive",
                authorization_base="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=["https://www.googleapis.com/auth/drive.file"],
                client_id=self.config.google_client_id,
                client_secret=self.config.google_client_secret,
                redirect_uri=self.config.google_redirect_uri,
            )
        if provider == "dropbox":
            return OAuthProviderConfig(
                name="dropbox",
                authorization_base="https://www.dropbox.com/oauth2/authorize",
                token_url="https://api.dropboxapi.com/oauth2/token",
                scopes=[
                    "files.content.read",
                    "files.content.write",
                    "files.metadata.read",
                ],
                client_id=self.config.dropbox_client_id,
                client_secret=self.config.dropbox_client_secret,
                redirect_uri=self.config.dropbox_redirect_uri,
            )
        if provider == "onedrive":
            return OAuthProviderConfig(
                name="onedrive",
                authorization_base="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=["Files.Read", "Files.ReadWrite", "User.Read"],
                client_id=self.config.onedrive_client_id,
                client_secret=self.config.onedrive_client_secret,
                redirect_uri=self.config.onedrive_redirect_uri,
            )
        raise ValueError(f"unsupported provider: {provider}")

    def get_authorization_url(self, provider: str, state: str) -> str:
        """Return the URL to send the tenant to for provider consent."""
        cfg = self._provider_config(provider)
        if not cfg.client_id:
            raise RuntimeError(f"{provider} client_id is not configured")

        params = {
            "client_id": cfg.client_id,
            "redirect_uri": cfg.redirect_uri,
            "response_type": "code",
            "scope": " ".join(cfg.scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        # Microsoft and Dropbox expect space-separated scopes too; Google uses +.
        # We keep a single string for all of them.
        if provider == "google_drive":
            params["scope"] = " ".join(cfg.scopes)
            params["include_granted_scopes"] = "false"

        return f"{cfg.authorization_base}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, provider: str, code: str) -> None:
        """Placeholder for Phase 3: exchange auth code for refresh/access token.

        This is intentionally not implemented without real credentials. The
        interface is committed now so the UI and tests can be written against it.
        """
        raise NotImplementedError(
            "Provider code exchange requires real credentials (Phase 3)."
        )
