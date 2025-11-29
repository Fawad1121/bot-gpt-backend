"""
API endpoint tests
"""
import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code in [200, 503]  # May fail if DB not connected
        data = response.json()
        assert "status" in data
        assert "database" in data


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


@pytest.mark.asyncio
async def test_create_conversation_validation():
    """Test conversation creation with validation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Missing required fields
        response = await client.post("/api/v1/conversations", json={})
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_conversations_requires_user_id():
    """Test that listing conversations requires user_id"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/conversations")
        assert response.status_code == 422  # Missing required parameter
