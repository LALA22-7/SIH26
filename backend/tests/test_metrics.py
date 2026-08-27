"""Tests for GET /api/metrics."""
import os
os.environ["ML_FORCE_STUB"] = "true"

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric_row import MetricRow


async def _seed_metrics(db: AsyncSession, event_id: str):
    """Insert metric rows with known error values for deterministic MAE tests."""
    base = datetime(2023, 6, 13, 0, 0, tzinfo=timezone.utc)
    rows = [
        MetricRow(
            metric_id=uuid.uuid4(),
            event_id=event_id,
            base_time=base + timedelta(hours=i * 6),
            horizon_hours=12,
            pred_lat=15.0 + i * 0.1,
            pred_lon=68.0,
            actual_lat=15.0 + i * 0.1 + 0.1,  # small offset → ~11 km error
            actual_lon=68.0,
            error_km=11.1,
            ground_truth_label="banding",
            predicted_label="banding",
        )
        for i in range(3)
    ] + [
        MetricRow(
            metric_id=uuid.uuid4(),
            event_id=event_id,
            base_time=base + timedelta(hours=i * 6),
            horizon_hours=24,
            pred_lat=16.0 + i * 0.1,
            pred_lon=67.8,
            actual_lat=16.0 + i * 0.1 + 0.2,
            actual_lon=67.8,
            error_km=22.2,
            ground_truth_label="eye",
            predicted_label="eye",
        )
        for i in range(3)
    ]
    for row in rows:
        db.add(row)
    await db.commit()


@pytest.mark.asyncio
async def test_metrics_no_data_returns_zeros(client: AsyncClient, seeded_event):
    response = await client.get("/api/metrics?event_id=biparjoy_2023")
    assert response.status_code == 200
    data = response.json()
    assert data["note"] == "no data"


@pytest.mark.asyncio
async def test_metrics_with_data_200(client: AsyncClient, seeded_event, db_session):
    await _seed_metrics(db_session, "biparjoy_2023")
    response = await client.get("/api/metrics?event_id=biparjoy_2023")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_dataset_counts(client: AsyncClient, seeded_event, db_session):
    await _seed_metrics(db_session, "biparjoy_2023")
    response = await client.get("/api/metrics?event_id=biparjoy_2023")
    data = response.json()
    assert data["dataset"]["forecasts"] == 6  # 3 T+12 + 3 T+24
    assert data["dataset"]["events"] == 1


@pytest.mark.asyncio
async def test_metrics_mae_t12(client: AsyncClient, seeded_event, db_session):
    await _seed_metrics(db_session, "biparjoy_2023")
    response = await client.get("/api/metrics?event_id=biparjoy_2023")
    data = response.json()
    # All T+12 rows have error_km=11.1 → MAE should be ~11.1
    assert data["track"]["mae_km_t12"] is not None
    assert abs(data["track"]["mae_km_t12"] - 11.1) < 0.1


@pytest.mark.asyncio
async def test_metrics_mae_t24(client: AsyncClient, seeded_event, db_session):
    await _seed_metrics(db_session, "biparjoy_2023")
    response = await client.get("/api/metrics?event_id=biparjoy_2023")
    data = response.json()
    assert data["track"]["mae_km_t24"] is not None
    assert abs(data["track"]["mae_km_t24"] - 22.2) < 0.1


@pytest.mark.asyncio
async def test_metrics_classification_accuracy(client: AsyncClient, seeded_event, db_session):
    await _seed_metrics(db_session, "biparjoy_2023")
    response = await client.get("/api/metrics?event_id=biparjoy_2023")
    data = response.json()
    # All rows have matching ground_truth_label and predicted_label → accuracy = 1.0
    assert data["classification"]["accuracy"] == 1.0
    assert data["classification"]["sample_count"] == 6


@pytest.mark.asyncio
async def test_metrics_schema_keys_present(client: AsyncClient, seeded_event, db_session):
    await _seed_metrics(db_session, "biparjoy_2023")
    response = await client.get("/api/metrics?event_id=biparjoy_2023")
    data = response.json()
    assert "dataset" in data
    assert "track" in data
    assert "classification" in data
    assert "uncertainty" in data
    assert "baseline" in data


@pytest.mark.asyncio
async def test_metrics_no_event_filter(client: AsyncClient, seeded_event, db_session):
    """Without event_id filter, should return aggregate across all events."""
    await _seed_metrics(db_session, "biparjoy_2023")
    response = await client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset"]["forecasts"] >= 6
