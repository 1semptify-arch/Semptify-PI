"""Async SQLAlchemy database setup for the real Core."""
from __future__ import annotations

from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import CoreConfig


class Database:
    """Manages the async engine and session factory."""

    def __init__(self, database_url: str | None = None) -> None:
        cfg = CoreConfig.from_env()
        self._url = database_url or cfg.database_url
        self._engine = create_async_engine(self._url)
        self._session_factory = sessionmaker(  # type: ignore[call-overload]
            bind=self._engine, class_=AsyncSession, expire_on_commit=False
        )

    @property
    def engine(self):
        return self._engine

    def session(self) -> AsyncSession:
        return cast(AsyncSession, self._session_factory())
