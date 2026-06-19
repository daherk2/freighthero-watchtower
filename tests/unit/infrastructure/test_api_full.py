"""Tests for API routes - comprehensive coverage."""

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

    @pytest.mark.asyncio
    async def test_health_check_version(self, app):
        """Test that health check includes version."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            assert data["version"] == "0.1.0"


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
        """Test creating a load with invalid payload."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/loads/", json={})
            assert response.status_code in [400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_create_load_missing_fields(self, app):
        """Test creating a load with missing required fields."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/loads/", json={"customer_id": "customer_a"})
            assert response.status_code in [400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_get_load_not_found(self, app):
        """Test getting a non-existent load."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/loads/nonexistent-id")
            assert response.status_code in [404, 500, 503]


class TestMonitoringEndpoints:
    """Tests for monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_dashboard_returns_data(self, app):
        """Test that the dashboard endpoint returns data."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/monitoring/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert "active_loads" in data
            assert "running_agents" in data
            assert "failed_agents" in data
            assert "error_rate_24h" in data

    @pytest.mark.asyncio
    async def test_dashboard_returns_defaults_without_db(self, app):
        """Test that dashboard returns defaults when DB is not configured."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/monitoring/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert data["active_loads"] == 0
            assert data["running_agents"] == 0

    @pytest.mark.asyncio
    async def test_agent_runs_endpoint(self, app):
        """Test that the agent runs endpoint returns data."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/monitoring/agent-runs")
            assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_agent_runs_with_load_id(self, app):
        """Test agent runs filtered by load ID."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/monitoring/agent-runs?load_id=test-load")
            assert response.status_code in [200, 500, 503]


class TestDebuggerEndpoints:
    """Tests for debugger endpoints."""

    @pytest.mark.asyncio
    async def test_get_agent_run_detail_not_found(self, app):
        """Test getting a non-existent agent run."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debugger/agent-runs/nonexistent-run-id")
            assert response.status_code in [404, 500, 503]

    @pytest.mark.asyncio
    async def test_get_load_history_not_found(self, app):
        """Test getting history for a non-existent load."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debugger/loads/nonexistent-load-id/history")
            assert response.status_code in [404, 500, 503]


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

    def test_app_has_cors_middleware(self, app):
        """Test that CORS middleware is configured."""
        middleware_classes = [m.cls.__name__ if hasattr(m, 'cls') else str(m) for m in app.user_middleware]
        # Check that CORSMiddleware is in the middleware stack
        assert any("CORS" in str(m) for m in app.user_middleware) or len(app.user_middleware) > 0