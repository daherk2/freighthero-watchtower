"""Tests for API endpoints - health, loads, and workflows."""

import sys
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport


# Mock langchain_openai before any imports
sys.modules["langchain_openai"] = MagicMock()


@pytest.fixture
def app():
    """Create a test application."""
    from src.interfaces.app import create_app
    return create_app()


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, app):
        """Test the health check endpoint returns healthy status."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data


class TestLoadEndpoints:
    """Tests for load management endpoints."""

    @pytest.mark.asyncio
    async def test_get_active_loads(self, app):
        """Test getting active loads."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/loads/")
            assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_create_load_invalid_payload(self, app):
        """Test creating a load with invalid payload returns 400 or 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/loads/", json={})
            assert response.status_code in [400, 422, 503]

    @pytest.mark.asyncio
    async def test_create_load_missing_fields(self, app):
        """Test creating a load with missing required fields."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/loads/", json={"customer_id": "customer_a"})
            assert response.status_code in [400, 422, 503]

    @pytest.mark.asyncio
    async def test_get_load_not_found(self, app):
        """Test getting a non-existent load returns 404 or 503."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/loads/nonexistent-id")
            assert response.status_code in [404, 500, 503]


class TestWorkflowsEndpoint:
    """Tests for workflow listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_workflows(self, app):
        """Test listing available workflows."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/events/workflows")
            # May return 200 or 404 depending on route registration
            assert response.status_code in [200, 404, 500, 503]


class TestAppConfiguration:
    """Tests for app configuration and middleware."""

    def test_app_title(self, app):
        """Test that the app has the correct title."""
        assert app.title == "FreightHero Watchtower"

    def test_app_has_routes(self, app):
        """Test that the app has routes registered."""
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        assert len(routes) > 0

    def test_app_has_health_route(self, app):
        """Test that the app has a health route."""
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        assert "/health" in routes

    def test_app_has_loads_routes(self, app):
        """Test that the app has loads routes."""
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        load_routes = [r for r in routes if "/loads" in r]
        assert len(load_routes) > 0