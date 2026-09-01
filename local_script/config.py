"""Config persistence for the local_script plugin."""
from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


class PluginConfig(BaseModel):
    """On-disk configuration for the local_script plugin.

    The plugin token is the only secret. Store it locally; never commit it.
    """

    core_url: str = Field(default="http://127.0.0.1:9000")
    plugin_id: str | None = Field(default=None)
    plugin_token: str | None = Field(default=None)
    packaging: str = Field(default="local_script")

    @classmethod
    def from_file(cls, path: str | Path | None = None) -> "PluginConfig":
        path = Path(path) if path else DEFAULT_CONFIG_PATH
        if not path.exists():
            return cls()
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def to_file(self, path: str | Path | None = None) -> None:
        path = Path(path) if path else DEFAULT_CONFIG_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(exclude_none=False), f, indent=2)
            f.write("\n")

    def apply_env(self) -> "PluginConfig":
        """Overlay environment variables on the loaded config."""
        if os.environ.get("SEMPIFY_PI_CORE_URL"):
            self.core_url = os.environ["SEMPIFY_PI_CORE_URL"]
        if os.environ.get("SEMPIFY_PI_PLUGIN_ID"):
            self.plugin_id = os.environ["SEMPIFY_PI_PLUGIN_ID"]
        if os.environ.get("SEMPIFY_PI_PLUGIN_TOKEN"):
            self.plugin_token = os.environ["SEMPIFY_PI_PLUGIN_TOKEN"]
        return self
