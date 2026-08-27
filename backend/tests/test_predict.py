"""Tests for POST /api/ps70/predict."""
import os
os.environ["ML_FORCE_STUB"] = "true"

import pytest
from httpx import AsyncClient


@pytest.fixture
def predict_body():
    return {
        "event_id": "biparjoy_2023",
        "start_timestamp": "2023-06-14T00:00:00Z",
    }


@pytest.mark.asyncio
async def test_predict_happy_path(client: AsyncClient, seeded_frame, predict_body):
    response = await client.post("/api/ps70/predict", json=predict_body)
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "biparjoy_2023"
    assert "base_time" in data
    assert "predictions" in data
    assert "uncertainty" in data
    assert "model" in data


@pytest.mark.asyncio
async def test_predict_has_two_steps(client: AsyncClient, seeded_frame, predict_body):
    response = await client.post("/api/ps70/predict", json=predict_body)
    data = response.json()
    assert len(data["predictions"]) == 2


@pytest.mark.asyncio
async def test_predict_step_schema(client: AsyncClient, seeded_frame, predict_body):
    response = await client.post("/api/ps70/predict", json=predict_body)
    data = response.json()
    for step in data["predictions"]:
        assert "valid_time" in step
        assert "center" in step
        assert "lat" in step["center"]
        assert "lon" in step["center"]
        assert "pattern" in step
        assert "label" in step["pattern"]
        assert "confidence" in step["pattern"]
        assert -90 <= step["center"]["lat"] <= 90
        assert -180 <= step["center"]["lon"] <= 180
        assert 0.0 <= step["pattern"]["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_predict_valid_times_are_future_of_base(client: AsyncClient, seeded_frame, predict_body):
    response = await client.post("/api/ps70/predict", json=predict_body)
    data = response.json()
    base = data["base_time"]
    for step in data["predictions"]:
        assert step["valid_time"] > base


@pytest.mark.asyncio
async def test_predict_uncertainty_block_present(client: AsyncClient, seeded_frame, predict_body):
    response = await client.post("/api/ps70/predict", json=predict_body)
    data = response.json()
    u = data["uncertainty"]
    assert "status" in u
    assert u["status"] == "provisional"
    assert "geometry" in u
    assert u["geometry"]["type"] == "Polygon"
    # Coverage target must NOT be set until calibration
    assert u.get("coverage_target") is None


@pytest.mark.asyncio
async def test_predict_uncertainty_polygon_has_coordinates(client: AsyncClient, seeded_frame, predict_body):
    response = await client.post("/api/ps70/predict", json=predict_body)
    data = response.json()
    coords = data["uncertainty"]["geometry"]["coordinates"]
    assert isinstance(coords, list)
    assert len(coords) > 0  # outer ring exists
    assert len(coords[0]) >= 4  # at least 4 points


@pytest.mark.asyncio
async def test_predict_stub_model_labeled(client: AsyncClient, seeded_frame, predict_body):
    response = await client.post("/api/ps70/predict", json=predict_body)
    data = response.json()
    assert "stub" in data["model"]["name"].lower()


@pytest.mark.asyncio
async def test_predict_invalid_event(client: AsyncClient, seeded_frame):
    body = {"event_id": "no_such_event", "start_timestamp": "2023-06-14T00:00:00Z"}
    response = await client.post("/api/ps70/predict", json=body)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_predict_no_timezone_rejected(client: AsyncClient, seeded_frame):
    body = {"event_id": "biparjoy_2023", "start_timestamp": "2023-06-14T00:00:00"}
    response = await client.post("/api/ps70/predict", json=body)
    assert response.status_code == 422
