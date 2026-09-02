"""OAuth flow helpers and provider token storage.

This module builds provider authorization URLs, exchanges authorization codes for
refresh/access tokens, and encrypts long-lived refresh tokens before they are
stored in the Core database.

Core never sees document bytes. The only bytes Core handles here are OAuth
tokens and short-lived provider metadata.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import urllib.parse
from dataclasses import dataclass
from typing import Any, cast

import httpx
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config import CoreConfig


def _derive_fernet_key(secret: str, salt: bytes = b"semptify-pi-oauth-v1") -> bytes:
    """Return a 32-byte base64-encoded Fernet key.

    If the secret is already a valid Fernet key, use it as-is. Otherwise derive
    one using PBKDF2 so plain-password-style secrets still work.
    """
    try:
        decoded = base64.urlsafe_b64decode(secret.encode("utf-8"))
        if len(decoded) == 32:
            return secret.encode("utf-8")
    except Exception:
        pass

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode("utf-8")))


@dataclass
class OAuthProviderConfig:
    name: str
    authorization_base: str
    token_url: str
    scopes: list[str]
    client_id: str
    client_secret: str
    redirect_uri: str


class TokenCrypto:
    """Encrypt/decrypt provider refresh tokens and OAuth state tokens."""

    def __init__(self, config: CoreConfig | None = None) -> None:
        self.config = config or CoreConfig.from_env()
        # Read the key at runtime so .env can be loaded after this module is
        # first imported (e.g. in tests that monkeypatch the env before import).
        secret = os.environ.get(
            "SEMPIFY_PI_ENCRYPTION_KEY", self.config.encryption_key
        )
        if not secret:
            raise RuntimeError(
                "SEMPIFY_PI_ENCRYPTION_KEY is not configured. "
                "Add it to .env (gitignored) or the host environment."
            )
        self._fernet = Fernet(_derive_fernet_key(secret))

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

    def create_state(
        self,
        tenant_id: str,
        provider: str,
        scopes: list[str] | None = None,
    ) -> str:
        payload = json.dumps(
            {
                "tenant_id": tenant_id,
                "provider": provider,
                "scopes": scopes or [],
                "nonce": secrets.token_urlsafe(16),
            }
        )
        return self.encrypt(payload)

    def verify_state(self, state: str) -> dict[str, Any]:
        try:
            return cast(dict[str, Any], json.loads(self.decrypt(state)))
        except Exception as exc:
            raise ValueError("invalid or tampered OAuth state") from exc


class OAuthManager:
    """Builds OAuth URLs, exchanges codes, and encrypts provider tokens."""

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
                authorization_base=(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
                ),
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=[
                    "Files.Read",
                    "Files.ReadWrite",
                    "User.Read",
                    "offline_access",
                ],
                client_id=self.config.onedrive_client_id,
                client_secret=self.config.onedrive_client_secret,
                redirect_uri=self.config.onedrive_redirect_uri,
            )
        raise ValueError(f"unsupported provider: {provider}")

    @property
    def crypto(self) -> TokenCrypto:
        return TokenCrypto(self.config)

    def provider_scopes(self, provider: str) -> list[str]:
        return list(self._provider_config(provider).scopes)

    def get_authorization_url(self, provider: str, state: str) -> str:
        """Return the URL to send the tenant to for provider consent."""
        cfg = self._provider_config(provider)
        if not cfg.client_id:
            raise RuntimeError(f"{provider} client_id is not configured")

        params: dict[str, str] = {
            "client_id": cfg.client_id,
            "redirect_uri": cfg.redirect_uri,
            "response_type": "code",
            "scope": " ".join(cfg.scopes),
            "state": state,
        }

        if provider == "google_drive":
            # Offline access and forced consent guarantee we get a refresh token.
            params["access_type"] = "offline"
            params["prompt"] = "consent"
            params["include_granted_scopes"] = "false"
        elif provider == "dropbox":
            # Dropbox uses token_access_type to request a refresh token.
            params["token_access_type"] = "offline"
        elif provider == "onedrive":
            params["response_mode"] = "query"
            params["prompt"] = "consent"

        # Use percent-encoding for spaces (%20) rather than '+' so all three
        # providers see a single space-delimited scope string.
        query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        return f"{cfg.authorization_base}?{query}"

    def _provider_token_data(self, provider: str) -> dict[str, str]:
        """Return common token request fields for the provider."""
        cfg = self._provider_config(provider)
        if not cfg.client_id or not cfg.client_secret:
            raise RuntimeError(f"{provider} OAuth credentials are not configured")
        return {
            "client_id": cfg.client_id,
            "client_secret": cfg.client_secret,
        }

    async def _token_request(self, provider: str, data: dict[str, str]) -> dict[str, Any]:
        """POST to the provider token endpoint and return the JSON response."""
        cfg = self._provider_config(provider)
        async with httpx.AsyncClient() as client:
            response = await client.post(cfg.token_url, data=data)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("OAuth token response must be an object")
            return cast(dict[str, Any], payload)

    async def exchange_code(self, provider: str, code: str) -> dict[str, Any]:
        """Exchange an OAuth authorization code for tokens."""
        data = self._provider_token_data(provider)
        data["grant_type"] = "authorization_code"
        data["code"] = code
        data["redirect_uri"] = self._provider_config(provider).redirect_uri

        # Microsoft requires the scope repeated on the token request; the other
        # providers accept or ignore it.
        if provider == "onedrive":
            data["scope"] = " ".join(self._provider_config(provider).scopes)

        return await self._token_request(provider, data)

    async def refresh_access_token(self, provider: str, refresh_token: str) -> dict[str, Any]:
        """Exchange a refresh token for a new access token."""
        data = self._provider_token_data(provider)
        data["grant_type"] = "refresh_token"
        data["refresh_token"] = refresh_token
        return await self._token_request(provider, data)
