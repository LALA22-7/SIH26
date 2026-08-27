"""Tests for POST /api/ps70/classify and GET /api/ps70/classifications/{event_id}."""
import os
os.environ["ML_FORCE_STUB"] = "true"

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models.event import Event
from app.models.satellite_frame import SatelliteFrame


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def classify_body():
    return {
        "event_id": "biparjoy_2023",
        "timestamp": "2023-06-14T12:00:00Z",
        "frame_id": "frame_001",
    }


# ── POST /api/ps70/classify ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_classify_happy_path(client: AsyncClient, seeded_frame, classify_body):
    response = await client.post("/api/ps70/classify", json=classify_body)
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "biparjoy_2023"
    assert "center" in data
    assert "lat" in data["center"]
    assert "lon" in data["center"]
    assert "pattern" in data
    assert "label" in data["pattern"]
    assert "confidence" in data["pattern"]
    assert "model" in data
    assert "source" in data
    assert data["source"]["frame_id"] == "frame_001"


@pytest.mark.asyncio
async def test_classify_response_schema(client: AsyncClient, seeded_frame, classify_body):
    response = await client.post("/api/ps70/classify", json=classify_body)
    data = response.json()
    # Coordinate ranges
    assert -90 <= data["center"]["lat"] <= 90
    assert -180 <= data["center"]["lon"] <= 180
    # Confidence range
    assert 0.0 <= data["pattern"]["confidence"] <= 1.0
    # Timestamp present
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_classify_stub_model_labeled(client: AsyncClient, seeded_frame, classify_body):
    response = await client.post("/api/ps70/classify", json=classify_body)
    data = response.json()
    # Stub mode must be clearly labeled
    assert "stub" in data["model"]["name"].lower()


@pytest.mark.asyncio
async def test_classify_invalid_event_id(client: AsyncClient, seeded_frame):
    body = {
        "event_id": "nonexistent_event",
        "timestamp": "2023-06-14T12:00:00Z",
        "frame_id": "frame_001",
    }
    response = await client.post("/api/ps70/classify", json=body)
    assert response.status_code == 422
    assert "event_id" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_classify_invalid_frame_id(client: AsyncClient, seeded_event):
    body = {
        "event_id": "biparjoy_2023",
        "timestamp": "2023-06-14T12:00:00Z",
        "frame_id": "nonexistent_frame",
    }
    response = await client.post("/api/ps70/classify", json=body)
    assert response.status_code == 422
    assert "frame_id" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_classify_missing_timezone_rejected(client: AsyncClient, seeded_frame):
    body = {
        "event_id": "biparjoy_2023",
        "timestamp": "2023-06-14T12:00:00",  # no Z / tz info
        "frame_id": "frame_001",
    }
    response = await client.post("/api/ps70/classify", json=body)
    # FastAPI will still parse naive ISO strings; our validator will reject them
    # Status is either 422 (Pydantic validation) or 200 with validation error
    # The validator on ClassifyRequest raises ValueError for naive datetimes
    assert response.status_code == 422


# ── GET /api/ps70/classifications/{event_id} ──────────────────────────────────

@pytest.mark.asyncio
async def test_list_classifications_empty(client: AsyncClient, seeded_event):
    response = await client.get("/api/ps70/classifications/biparjoy_2023")
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "biparjoy_2023"
    assert data["count"] == 0
    assert data["classifications"] == []


@pytest.mark.asyncio
async def test_list_classifications_after_classify(client: AsyncClient, seeded_frame, classify_body):
    # First classify
    await client.post("/api/ps70/classify", json=classify_body)
    # Then list
    response = await client.get("/api/ps70/classifications/biparjoy_2023")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["classifications"][0]["event_id"] == "biparjoy_2023"


@pytest.mark.asyncio
async def test_list_classifications_sorted_by_timestamp(client: AsyncClient, seeded_frame):
    """Multiple classifications must be returned sorted ascending by timestamp."""
    body1 = {"event_id": "biparjoy_2023", "timestamp": "2023-06-14T06:00:00Z", "frame_id": "frame_001"}
    body2 = {"event_id": "biparjoy_2023", "timestamp": "2023-06-14T12:00:00Z", "frame_id": "frame_001"}
    await client.post("/api/ps70/classify", json=body1)
    await client.post("/api/ps70/classify", json=body2)

    response = await client.get("/api/ps70/classifications/biparjoy_2023")
    data = response.json()
    assert data["count"] == 2
    ts_list = [r["timestamp"] for r in data["classifications"]]
    assert ts_list == sorted(ts_list)


@pytest.mark.asyncio
async def test_list_classifications_unknown_event(client: AsyncClient):
    response = await client.get("/api/ps70/classifications/unknown_event")
    assert response.status_code == 404
