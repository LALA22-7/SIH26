"""
Shared pytest fixtures for the CycloneWatch backend test suite.

Uses an in-memory SQLite database for unit/integration tests so that
tests run without a live PostgreSQL instance.

GeoAlchemy2 Geometry columns are swapped to plain sqlalchemy.Text
before any ORM model is imported, so SQLite can create all tables
without requiring PostGIS or SpatiaLite.
"""
import os

# ── Step 1: set SQLite URLs BEFORE any app module imports ────────────────────
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_SYNC_URL"] = "sqlite:///:memory:"
os.environ["DEBUG"] = "false"

# ── Step 2: replace GeoAlchemy2 Geometry with plain Text for SQLite ─────────
import sqlalchemy as sa
import geoalchemy2

# Patch Geometry so it behaves as Text in DDL (SQLite compatible)
class _TextGeometry(sa.Text):
    """Thin Text subclass that masquerades as GeoAlchemy2 Geometry for testing."""
    def __init__(self, *args, **kwargs):
        super().__init__()

geoalchemy2.Geometry = _TextGeometry
geoalchemy2.types.Geometry = _TextGeometry
# Also patch the submodule reference used in model imports
import geoalchemy2.types as _geo_types
_geo_types.Geometry = _TextGeometry

from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.base import Base
# Import all models to register them with Base.metadata
from app.models import Event, SatelliteFrame, Classification, Prediction, MetricRow  # noqa: F401
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Fresh in-memory SQLite engine + schema for every test function."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Fresh session per test, always rolled back."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with DB dependency injected as in-memory SQLite session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Seed helpers ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function")
async def seeded_event(db_session: AsyncSession):
    """Insert a minimal Event row."""
    event = Event(
        event_id="biparjoy_2023",
        name="Biparjoy",
        year=2023,
        basin="NI",
        start_time=datetime(2023, 6, 6, tzinfo=timezone.utc),
        end_time=datetime(2023, 6, 16, tzinfo=timezone.utc),
        notes="Primary demo event",
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)
    return event


@pytest_asyncio.fixture(scope="function")
async def seeded_frame(db_session: AsyncSession, seeded_event):
    """Insert a minimal SatelliteFrame row."""
    frame = SatelliteFrame(
        frame_id="frame_001",
        event_id="biparjoy_2023",
        timestamp=datetime(2023, 6, 14, 12, 0, tzinfo=timezone.utc),
        channels={"ir": "path/ir.tif", "water_vapor": "path/wv.tif"},
        file_paths={"ir": "/data/biparjoy_2023-06-14T1200Z_ir_insat.tif"},
        crs="EPSG:4326",
        bbox=[60.0, 5.0, 80.0, 25.0],
        resolution={"width": 512, "height": 512},
        source="INSAT-3D",
        local_path=None,
    )
    db_session.add(frame)
    await db_session.commit()
    await db_session.refresh(frame)
    return frame
