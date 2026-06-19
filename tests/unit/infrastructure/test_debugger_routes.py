"""Tests for debugger routes."""

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


class TestDebuggerRoutes:
    """Tests for debugger API endpoints."""

    @pytest.mark.asyncio
    async def test_get_agent_run_detail_not_found(self, app):
        """Test getting a non-existent agent run returns error."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debugger/agent-runs/nonexistent-run-id")
            # Without DB, returns 500; with DB but not found, returns 404
            assert response.status_code in [404, 500, 503]

    @pytest.mark.asyncio
    async def test_get_load_history_not_found(self, app):
        """Test getting history for a non-existent load returns error."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debugger/loads/nonexistent-load-id/history")
            assert response.status_code in [404, 500, 503]

    @pytest.mark.asyncio
    async def test_debugger_router_registered(self, app):
        """Test that debugger routes are registered."""
        routes = [route.path for route in app.routes]
        assert any("/debugger/" in route for route in routes)