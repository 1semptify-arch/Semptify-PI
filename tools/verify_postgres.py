"""Verify the agent can connect to the local PostgreSQL 16 instance."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


def _load_env_file() -> None:
    """Load a .env file from the repo root if it exists."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key not in os.environ:
                os.environ[key] = value


def _to_asyncpg_dsn(url: str) -> str:
    """Convert SQLAlchemy-style postgresql+asyncpg URL to an asyncpg DSN."""
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url[len("postgresql+asyncpg://"):]
    return url


async def main() -> int:
    _load_env_file()
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")
        return 1

    dsn = _to_asyncpg_dsn(url)
    try:
        import asyncpg
    except ImportError as exc:
        print("asyncpg is not installed. Install it with: pip install asyncpg")
        return 1

    try:
        conn = await asyncpg.connect(dsn=dsn)
        result = await conn.fetch("SELECT 1 AS connected;")
        print(f"OK: connected to {conn.get_server_version()}")
        print(f"Result: {result[0]['connected']}")
        await conn.close()
        return 0
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
