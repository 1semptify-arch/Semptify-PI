"""Seed the real Core database with the Phase 2 plugin manifest(s)."""
from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import PluginManifest


async def seed_manifests(session: AsyncSession) -> None:
    """Insert the reference plugins if they do not exist."""
    manifests = [
        {
            "id": "example-document-organizer",
            "plugin_id": "example-document-organizer",
            "name": "Document Organizer",
            "version": "1.0.0",
            "description": "Sorts and labels documents in your Semptify vault.",
            "author": "Semptify",
            "license": "AGPL-3.0",
            "homepage_url": "https://semptify.org/plugins/example-document-organizer",
            "packaging": ["browser_extension", "local_script"],
            "required_scopes": ["vault:read", "vault:write", "documents:capability"],
            "optional_scopes": ["context:read"],
            "api_version": "v1",
            "downloads": {
                "browser_extension": {
                    "download_url": "https://github.com/1semptify-arch/Semptify-PI/releases/download/v0.1.0/example-document-organizer.zip",
                    "chrome_web_store_url": "https://chromewebstore.google.com/detail/example-document-organizer",
                    "firefox_addon_url": "https://addons.mozilla.org/en-US/firefox/addon/example-document-organizer",
                },
                "local_script": {
                    "download_url": "https://github.com/1semptify-arch/Semptify-PI/releases/download/v0.1.0/example-document-organizer.py",
                    "python": "https://github.com/1semptify-arch/Semptify-PI/releases/download/v0.1.0/example-document-organizer.py",
                },
            },
            "connect": {
                "browser_extension_origin": "chrome-extension://example-document-organizer",
                "local_script_config_template": '{"core_url": "https://plugins.semptify.org", "plugin_token": "<PASTE TOKEN HERE>"}',
            },
            "icon_url": "https://semptify.org/static/icons/example-document-organizer.svg",
            "status": "approved",
        },
    ]

    for data in manifests:
        stmt = select(PluginManifest).where(PluginManifest.plugin_id == data["plugin_id"])
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            continue

        manifest = PluginManifest(
            id=data["id"],
            plugin_id=data["plugin_id"],
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data["author"],
            license=data["license"],
            homepage_url=data["homepage_url"],
            packaging=json.dumps(data["packaging"]),
            required_scopes=json.dumps(data["required_scopes"]),
            optional_scopes=json.dumps(data["optional_scopes"]),
            api_version=data["api_version"],
            downloads=json.dumps(data["downloads"]),
            connect=json.dumps(data["connect"]),
            icon_url=data["icon_url"],
            status=data["status"],
        )
        session.add(manifest)
    await session.flush()
