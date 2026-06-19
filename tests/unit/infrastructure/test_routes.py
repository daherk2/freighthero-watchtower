"""Tests for API routes - loads, events, monitoring, debugger."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.domain.enums import CustomerId, EventType, LoadState
from src.domain.models import Load, Event
from src.domain.exceptions import LoadNotFoundError, InvalidEventError


def make_load(**overrides):
    defaults = dict(
        load_id="load-1",
        customer_id=CustomerId.CUSTOMER_A,
        external_load_id="ext-1",
        current_state=LoadState.DISPATCHED,
        load_data={"origin": "A", "destination": "B"},
    )
    defaults.update(overrides)
    return Load(**defaults)


class TestLoadsRoute:
    """Tests for loads route handler logic."""

    @pytest.mark.asyncio
    async def test_load_to_dict_conversion(self):
        """Test that Load model converts to dict correctly."""
        load = make_load()
        from src.application.services.load_service import LoadService
        mock_repo = AsyncMock()
        service = LoadService(load_repo=mock_repo)
        result = service._load_to_dict(load)
        assert result["load_id"] == "load-1"
        assert result["customer_id"] == "customer_a"
        assert result["current_state"] == "dispatched"
        assert result["external_load_id"] == "ext-1"

    @pytest.mark.asyncio
    async def test_load_to_dict_with_enum_values(self):
        """Test that enum values are properly serialized."""
        load = make_load(current_state=LoadState.ON_ROUTE_TO_DELIVERY)
        from src.application.services.load_service import LoadService
        mock_repo = AsyncMock()
        service = LoadService(load_repo=mock_repo)
        result = service._load_to_dict(load)
        assert result["current_state"] == "on_route_to_delivery"


class TestEventProcessorValidation:
    """Tests for event validation logic used by routes."""

    @pytest.mark.asyncio
    async def test_validate_event_active_state(self):
        """Test that events in active states are valid."""
        from src.application.services.event_processor import EventProcessor
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()

        for state in [LoadState.DISPATCHED, LoadState.ON_ROUTE_TO_DELIVERY, LoadState.AT_DELIVERY, LoadState.CONFIRM_DELIVERY]:
            load = make_load(current_state=state)
            event = Event(
                event_id="evt-1",
                event_type=EventType.INBOUND_COMMUNICATION,
                load_id="load-1",
                customer_id=CustomerId.CUSTOMER_A,
                occurred_at=datetime.now(timezone.utc).isoformat(),
                event_data={"message": "test"},
            )
            mock_event_repo.get_by_id = AsyncMock(return_value=event)
            mock_load_repo.get_by_id = AsyncMock(return_value=load)
            mock_event_repo.mark_processed = AsyncMock()

            processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
            # Should not raise
            await processor.process("evt-1", "load-1")

    @pytest.mark.asyncio
    async def test_validate_event_delivered_state_raises(self):
        """Test that events in DELIVERED state are invalid."""
        from src.application.services.event_processor import EventProcessor
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()

        delivered_load = make_load(current_state=LoadState.DELIVERED)
        event = Event(
            event_id="evt-1",
            event_type=EventType.INBOUND_COMMUNICATION,
            load_id="load-1",
            customer_id=CustomerId.CUSTOMER_A,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            event_data={"message": "test"},
        )
        mock_event_repo.get_by_id = AsyncMock(return_value=event)
        mock_load_repo.get_by_id = AsyncMock(return_value=delivered_load)

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        with pytest.raises(InvalidEventError):
            await processor.process("evt-1", "load-1")

    @pytest.mark.asyncio
    async def test_validate_event_pod_collected_state_raises(self):
        """Test that events in POD_COLLECTED state are invalid."""
        from src.application.services.event_processor import EventProcessor
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()

        pod_load = make_load(current_state=LoadState.POD_COLLECTED)
        event = Event(
            event_id="evt-1",
            event_type=EventType.INBOUND_COMMUNICATION,
            load_id="load-1",
            customer_id=CustomerId.CUSTOMER_A,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            event_data={"message": "test"},
        )
        mock_event_repo.get_by_id = AsyncMock(return_value=event)
        mock_load_repo.get_by_id = AsyncMock(return_value=pod_load)

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        with pytest.raises(InvalidEventError):
            await processor.process("evt-1", "load-1")


class TestLoadServiceTransition:
    """Tests for LoadService state transitions."""

    @pytest.mark.asyncio
    async def test_transition_dispatched_to_on_route(self):
        """Test valid state transition."""
        from src.application.services.load_service import LoadService
        mock_repo = AsyncMock()
        load = make_load(current_state=LoadState.DISPATCHED)
        mock_repo.get_by_id = AsyncMock(return_value=load)
        mock_repo.save = AsyncMock(return_value=load)

        service = LoadService(load_repo=mock_repo)
        result = await service.transition_state("load-1", LoadState.ON_ROUTE_TO_DELIVERY)
        assert result.from_state == LoadState.DISPATCHED
        assert result.to_state == LoadState.ON_ROUTE_TO_DELIVERY

    @pytest.mark.asyncio
    async def test_transition_invalid_raises(self):
        """Test invalid state transition raises error."""
        from src.application.services.load_service import LoadService
        from src.domain.exceptions import InvalidStateTransitionError
        mock_repo = AsyncMock()
        load = make_load(current_state=LoadState.DISPATCHED)
        mock_repo.get_by_id = AsyncMock(return_value=load)

        service = LoadService(load_repo=mock_repo)
        with pytest.raises(InvalidStateTransitionError):
            # DISPATCHED -> DELIVERED is not a valid transition
            await service.transition_state("load-1", LoadState.DELIVERED)


class TestAppHealthCheck:
    """Tests for app health check."""

    def test_health_check_response(self):
        """Test that health check returns correct structure."""
        from src.interfaces.app import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"