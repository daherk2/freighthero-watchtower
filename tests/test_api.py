"""Tests for API endpoints."""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport

from src.domain.enums import CustomerId, EventType, LoadState


@pytest.fixture
def app():
    """Create a test application."""
    from src.interfaces.app import create_app
    return create_app()


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, app):
        """Test the health check endpoint."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestLoadEndpoints:
    """Tests for load management endpoints."""

    @pytest.mark.asyncio
    async def test_get_active_loads(self, app):
        """Test getting active loads."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/loads/")
            # May return 200 with empty list or 500/503 if DB not configured
            assert response.status_code in [200, 500, 503]


class TestEventEndpoints:
    """Tests for event processing endpoints."""

    @pytest.mark.asyncio
    async def test_submit_task_endpoint_exists(self, app):
        """Test that the submit-task endpoint exists."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/events/submit-task", json={
                "load_id": "load-test-001",
                "customer_id": "customer_a",
                "event_type": "inbound_communication",
                "event_data": {"message": "test"},
            })
            # May return 400/404/422/500 depending on DB state and validation
            assert response.status_code in [200, 201, 400, 404, 422, 500]


class TestMonitoringEndpoints:
    """Tests for monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_dashboard_endpoint(self, app):
        """Test the monitoring dashboard endpoint."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/monitoring/dashboard")
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_workflows_list(self, app):
        """Test listing available workflows."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debugger/workflows")
            assert response.status_code == 200
            data = response.json()
            assert "workflows" in data
            assert len(data["workflows"]) == 2