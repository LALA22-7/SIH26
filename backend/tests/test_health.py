"""Tests for GET /health."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # db status is either "ok" or "degraded" — both are valid responses
    assert data["db"] in ("ok", "degraded")


@pytest.mark.asyncio
async def test_health_has_correct_keys(client: AsyncClient):
    response = await client.get("/health")
    data = response.json()
    assert "status" in data
    assert "db" in data


@pytest.mark.asyncio
async def test_health_status_is_string(client: AsyncClient):
    response = await client.get("/health")
    data = response.json()
    assert isinstance(data["status"], str)
    assert isinstance(data["db"], str)
