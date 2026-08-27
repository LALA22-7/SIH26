"""Tests for GET /api/replay/{event_id}."""
import os
os.environ["ML_FORCE_STUB"] = "true"

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric_row import MetricRow
from app.models.prediction import Prediction


# ── Seed helper: insert predictions + metrics for replay ─────────────────────

async def _seed_replay_data(db: AsyncSession, event_id: str):
    """Insert minimal predictions and metric rows for replay tests."""
    base = datetime(2023, 6, 13, 0, 0, tzinfo=timezone.utc)

    for i in range(2):  # 2 analysis times
        bt = base + timedelta(hours=i * 6)

        # T+12 prediction
        db.add(Prediction(
            prediction_id=uuid.uuid4(),
            event_id=event_id,
            base_time=bt,
            valid_time=bt + timedelta(hours=12),
            pred_lat=15.2 + i * 0.5,
            pred_lon=68.4 - i * 0.3,
            pattern_label="banding",
            pattern_confidence=0.72,
            model_name="ps70-temporal-stub",
            model_version="0.1.0",
            uncertainty_status="provisional",
            uncertainty_geom=None,
        ))

        # T+24 prediction
        db.add(Prediction(
            prediction_id=uuid.uuid4(),
            event_id=event_id,
            base_time=bt,
            valid_time=bt + timedelta(hours=24),
            pred_lat=16.0 + i * 0.5,
            pred_lon=67.8 - i * 0.3,
            pattern_label="eye",
            pattern_confidence=0.64,
            model_name="ps70-temporal-stub",
            model_version="0.1.0",
            uncertainty_status="provisional",
            uncertainty_geom=None,
        ))

        # Metric rows with actuals
        for h in [12, 24]:
            db.add(MetricRow(
                metric_id=uuid.uuid4(),
                event_id=event_id,
                base_time=bt,
                horizon_hours=h,
                pred_lat=15.2 + i * 0.5 + (h / 100),
                pred_lon=68.4 - i * 0.3,
                actual_lat=15.3 + i * 0.5,
                actual_lon=68.3 - i * 0.3,
                error_km=55.0 + h,
                ground_truth_label="banding",
                predicted_label="banding",
            ))

    await db.commit()


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_replay_unknown_event(client: AsyncClient):
    response = await client.get("/api/replay/nonexistent_event")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_replay_empty_event(client: AsyncClient, seeded_event):
    """Event exists but has no predictions yet — returns empty steps."""
    response = await client.get("/api/replay/biparjoy_2023")
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "biparjoy_2023"
    assert data["total_steps"] == 0
    assert data["steps"] == []


@pytest.mark.asyncio
async def test_replay_returns_correct_step_count(client: AsyncClient, seeded_event, db_session):
    await _seed_replay_data(db_session, "biparjoy_2023")
    response = await client.get("/api/replay/biparjoy_2023")
    assert response.status_code == 200
    data = response.json()
    assert data["total_steps"] == 2
    assert len(data["steps"]) == 2


@pytest.mark.asyncio
async def test_replay_steps_sorted_ascending(client: AsyncClient, seeded_event, db_session):
    await _seed_replay_data(db_session, "biparjoy_2023")
    response = await client.get("/api/replay/biparjoy_2023")
    data = response.json()
    times = [s["time"] for s in data["steps"]]
    assert times == sorted(times)


@pytest.mark.asyncio
async def test_replay_step_has_required_keys(client: AsyncClient, seeded_event, db_session):
    await _seed_replay_data(db_session, "biparjoy_2023")
    response = await client.get("/api/replay/biparjoy_2023")
    data = response.json()
    for step in data["steps"]:
        assert "time" in step
        assert "prediction" in step
        assert "actual" in step
        assert "errors" in step


@pytest.mark.asyncio
async def test_replay_errors_are_floats(client: AsyncClient, seeded_event, db_session):
    await _seed_replay_data(db_session, "biparjoy_2023")
    response = await client.get("/api/replay/biparjoy_2023")
    data = response.json()
    for step in data["steps"]:
        errs = step["errors"]
        if errs.get("t12_km") is not None:
            assert isinstance(errs["t12_km"], (int, float))
        if errs.get("t24_km") is not None:
            assert isinstance(errs["t24_km"], (int, float))


@pytest.mark.asyncio
async def test_replay_no_ml_calls(client: AsyncClient, seeded_event, db_session, monkeypatch):
    """Replay must not call ML adapter at serve time."""
    call_count = {"n": 0}

    def mock_classify(*args, **kwargs):
        call_count["n"] += 1
        return {}

    monkeypatch.setattr("app.services.ml_adapter.run_classify", mock_classify)

    await _seed_replay_data(db_session, "biparjoy_2023")
    await client.get("/api/replay/biparjoy_2023")
    assert call_count["n"] == 0, "Replay endpoint must not call ML adapter"
