"""Async SQLAlchemy engine and session factory.

The engine is created lazily on first access so that test environments
can override DATABASE_URL via environment variables before any import
triggers engine construction.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


@lru_cache(maxsize=1)
def _get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


@lru_cache(maxsize=1)
def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=_get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


# Convenience accessors used by main.py lifespan
@property
def engine() -> AsyncEngine:  # type: ignore[misc]
    return _get_engine()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session per request."""
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine() -> None:
    """Dispose the async engine pool. Called on app shutdown."""
    _get_engine.cache_clear()
    _get_session_factory.cache_clear()
