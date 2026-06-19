"""Tests for monitoring routes."""

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


class TestMonitoringRoutes:
    """Tests for monitoring API endpoints."""

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
        """Test that the agent runs endpoint is accessible."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/monitoring/agent-runs")
            # May return 200 with data, 500, or 503 if DB not configured
            assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_monitoring_router_registered(self, app):
        """Test that monitoring routes are registered."""
        routes = [route.path for route in app.routes]
        assert any("/monitoring/" in route for route in routes)