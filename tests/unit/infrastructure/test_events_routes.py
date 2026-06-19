"""Tests for event routes - unit tests for route handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.domain.enums import CustomerId, EventType, LoadState
from src.domain.models import Event, Load
from src.application.services.event_processor import EventProcessor


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


def make_event(**overrides):
    defaults = dict(
        event_id="evt-1",
        event_type=EventType.INBOUND_COMMUNICATION,
        load_id="load-1",
        customer_id=CustomerId.CUSTOMER_A,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        event_data={"message": "I'll arrive in 30 min"},
    )
    defaults.update(overrides)
    return Event(**defaults)


class TestEventProcessorDetermineWorkflow:
    """Test workflow determination logic used by event routes."""

    def test_dispatched_routes_to_eta(self):
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.DISPATCHED)
        event = make_event(event_type=EventType.INBOUND_COMMUNICATION)
        assert processor._determine_workflow(event, load) == "delivery_eta_checkpoint"

    def test_on_route_routes_to_eta(self):
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.ON_ROUTE_TO_DELIVERY)
        event = make_event(event_type=EventType.TRACKING)
        assert processor._determine_workflow(event, load) == "delivery_eta_checkpoint"

    def test_at_delivery_routes_to_confirm(self):
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.AT_DELIVERY)
        event = make_event(event_type=EventType.INBOUND_COMMUNICATION)
        assert processor._determine_workflow(event, load) == "confirm_delivery"

    def test_confirm_delivery_routes_to_confirm(self):
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.CONFIRM_DELIVERY)
        event = make_event(event_type=EventType.INBOUND_COMMUNICATION)
        assert processor._determine_workflow(event, load) == "confirm_delivery"

    def test_load_update_routes_to_eta(self):
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.DISPATCHED)
        event = make_event(event_type=EventType.LOAD_UPDATE)
        assert processor._determine_workflow(event, load) == "delivery_eta_checkpoint"


class TestEventProcessorValidation:
    """Test event validation logic."""

    @pytest.mark.asyncio
    async def test_validate_event_wrong_load_raises(self):
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()
        from src.domain.exceptions import InvalidEventError
        event = make_event(load_id="load-OTHER")
        load = make_load()
        mock_event_repo.get_by_id = AsyncMock(return_value=event)
        mock_load_repo.get_by_id = AsyncMock(return_value=load)

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        with pytest.raises(InvalidEventError):
            await processor.process("evt-1", "load-1")

    @pytest.mark.asyncio
    async def test_validate_event_delivered_state_raises(self):
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()
        from src.domain.exceptions import InvalidEventError
        delivered_load = make_load(current_state=LoadState.DELIVERED)
        event = make_event()
        mock_event_repo.get_by_id = AsyncMock(return_value=event)
        mock_load_repo.get_by_id = AsyncMock(return_value=delivered_load)

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        with pytest.raises(InvalidEventError):
            await processor.process("evt-1", "load-1")