"""Tests for GET /api/ps70/frames/{frame_id}."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_frame_returns_metadata(client: AsyncClient, seeded_frame):
    response = await client.get("/api/ps70/frames/frame_001")
    assert response.status_code == 200
    data = response.json()
    assert data["frame_id"] == "frame_001"
    assert data["event_id"] == "biparjoy_2023"
    assert "ir" in data["channels"]
    assert data["crs"] == "EPSG:4326"
    assert len(data["bbox"]) == 4


@pytest.mark.asyncio
async def test_get_frame_not_found(client: AsyncClient, seeded_event):
    response = await client.get("/api/ps70/frames/nonexistent_frame")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_frame_image_no_local_path(client: AsyncClient, seeded_frame):
    """Frame exists in DB but has no local_path — should return 404 for image format."""
    response = await client.get("/api/ps70/frames/frame_001?format=image")
    assert response.status_code == 404
    data = response.json()
    assert "local file path" in data["detail"].lower() or "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_frame_timestamp_present(client: AsyncClient, seeded_frame):
    response = await client.get("/api/ps70/frames/frame_001")
    data = response.json()
    assert "timestamp" in data
    assert "2023" in data["timestamp"]


@pytest.mark.asyncio
async def test_get_frame_resolution_present(client: AsyncClient, seeded_frame):
    response = await client.get("/api/ps70/frames/frame_001")
    data = response.json()
    assert data["resolution"]["width"] == 512
    assert data["resolution"]["height"] == 512
