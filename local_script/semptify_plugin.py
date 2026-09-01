"""CLI entry point for the local_script reference plugin."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from local_script.client import SemptifyPluginClient
from local_script.config import DEFAULT_CONFIG_PATH, PluginConfig


def _load_config(config_path: str | None) -> PluginConfig:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    return PluginConfig.from_file(path).apply_env()


def _save_config(config: PluginConfig, config_path: str | None) -> None:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    config.to_file(path)


def _client_from_config(config: PluginConfig) -> SemptifyPluginClient:
    return SemptifyPluginClient(
        core_url=config.core_url,
        plugin_token=config.plugin_token,
    )


def _session_token(args: argparse.Namespace) -> str:
    token = (
        args.session_token
        or os.environ.get("SEMPIFY_PI_SESSION_TOKEN")
        or ""
    )
    if not token:
        print(
            "Error: a session token is required. "
            "Pass --session-token or set SEMPIFY_PI_SESSION_TOKEN.",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def cmd_list(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    client = _client_from_config(config)
    try:
        data = client.list_plugins(packaging=args.packaging)
        print(json.dumps(data, indent=2))
        return 0
    finally:
        client.close()


def cmd_connect(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    session = _session_token(args)
    client = SemptifyPluginClient(core_url=config.core_url)
    try:
        data = client.connect(
            plugin_id=args.plugin_id,
            session_token=session,
            packaging=args.packaging,
            label=args.label,
        )
        config.plugin_id = data["plugin_id"]
        config.plugin_token = data["token"]
        _save_config(config, args.config)
        print(json.dumps({"plugin_id": data["plugin_id"], "token_id": data["token_id"], "scopes": data["scopes"]}, indent=2))
        return 0
    finally:
        client.close()


def cmd_me(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    client = _client_from_config(config)
    try:
        data = client.me()
        print(json.dumps(data, indent=2))
        return 0
    finally:
        client.close()


def cmd_download_url(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    client = _client_from_config(config)
    try:
        data = client.download_url(args.file_id)
        print(json.dumps(data, indent=2))
        return 0
    finally:
        client.close()


def cmd_upload_url(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    client = _client_from_config(config)
    try:
        data = client.upload_url(args.filename, parent_folder=args.parent_folder)
        print(json.dumps(data, indent=2))
        return 0
    finally:
        client.close()


def cmd_complete(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    client = _client_from_config(config)
    try:
        data = client.complete_upload(
            completion_token=args.completion_token,
            provider_file_id=args.provider_file_id,
            filename=args.filename,
            size=args.size,
        )
        print(json.dumps(data, indent=2))
        return 0
    finally:
        client.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local-plugin",
        description="Semptify-PI local_script reference plugin.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to plugin config file (default: local_script/config.json).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List approved plugins.")
    list_cmd.add_argument(
        "--packaging",
        default=None,
        choices=["browser_extension", "desktop_app", "local_script"],
        help="Filter by packaging type.",
    )
    list_cmd.set_defaults(func=cmd_list)

    connect_cmd = sub.add_parser("connect", help="Connect this plugin and save the token.")
    connect_cmd.add_argument("plugin_id", help="Plugin to connect (e.g. example-document-organizer).")
    connect_cmd.add_argument(
        "--session-token",
        default=None,
        help="Tenant session token for issuing the plugin token.",
    )
    connect_cmd.add_argument(
        "--packaging",
        default="local_script",
        choices=["browser_extension", "desktop_app", "local_script"],
        help="Packaging type to request.",
    )
    connect_cmd.add_argument("--label", default=None, help="Optional token label.")
    connect_cmd.set_defaults(func=cmd_connect)

    me_cmd = sub.add_parser("me", help="Show current plugin context.")
    me_cmd.set_defaults(func=cmd_me)

    download_cmd = sub.add_parser("download-url", help="Get a direct download URL for a file.")
    download_cmd.add_argument("file_id", help="File identifier in the vault.")
    download_cmd.set_defaults(func=cmd_download_url)

    upload_cmd = sub.add_parser("upload-url", help="Get a direct upload URL.")
    upload_cmd.add_argument("filename", help="Filename to upload.")
    upload_cmd.add_argument("--parent-folder", default=None, help="Vault parent folder.")
    upload_cmd.set_defaults(func=cmd_upload_url)

    complete_cmd = sub.add_parser("complete", help="Record a completed upload.")
    complete_cmd.add_argument("completion_token", help="Completion token from upload-url.")
    complete_cmd.add_argument("provider_file_id", help="Provider-side file id.")
    complete_cmd.add_argument("filename", help="Filename.")
    complete_cmd.add_argument("--size", type=int, default=None, help="File size in bytes.")
    complete_cmd.set_defaults(func=cmd_complete)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
