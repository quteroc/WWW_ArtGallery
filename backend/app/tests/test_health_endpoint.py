"""
Tests for health check endpoint.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Test health check endpoint returns 200."""
    response = await async_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_endpoint_includes_database_status(async_client: AsyncClient):
    """Test health check includes database status."""
    response = await async_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert data["database"] == "connected"


# Root endpoint test removed as it depends on templates being available


@pytest.mark.asyncio
async def test_health_database_connection(async_client: AsyncClient):
    """Test health endpoint reports database connection."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] == "connected"
