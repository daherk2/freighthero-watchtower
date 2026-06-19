"""Unit tests for domain models."""

import uuid
from datetime import datetime, timezone

import pytest

from src.domain.enums import CustomerId, EventType, LoadState, SenderType, Channel
from src.domain.models import Load, Event, InboundCommunicationEvent, TrackingEvent
from src.domain.exceptions import InvalidStateTransitionError, LoadNotFoundError


class TestLoad:
    """Tests for the Load domain model."""

    def test_create_load(self, sample_load):
        """Test creating a load with valid data."""
        load = Load(**sample_load)
        assert load.load_id == sample_load["load_id"]
        assert load.customer_id == CustomerId.CUSTOMER_A
        assert load.current_state == LoadState.ON_ROUTE_TO_DELIVERY

    def test_transition_to_valid_state(self, sample_load):
        """Test valid state transitions."""
        load = Load(**sample_load)

        # DISPATCHED -> ON_ROUTE_TO_DELIVERY
        load.current_state = LoadState.DISPATCHED
        load.transition_to(LoadState.ON_ROUTE_TO_DELIVERY)
        assert load.current_state == LoadState.ON_ROUTE_TO_DELIVERY

    def test_transition_to_at_delivery(self, sample_load):
        """Test transition to at_delivery state."""
        load = Load(**sample_load)
        load.transition_to(LoadState.AT_DELIVERY)
        assert load.current_state == LoadState.AT_DELIVERY

    def test_transition_to_confirm_delivery(self, sample_load):
        """Test transition to confirm_delivery state."""
        load = Load(**sample_load)
        load.transition_to(LoadState.CONFIRM_DELIVERY)
        assert load.current_state == LoadState.CONFIRM_DELIVERY

    def test_transition_to_delivered(self, sample_load):
        """Test transition to delivered state."""
        load = Load(**sample_load)
        load.current_state = LoadState.CONFIRM_DELIVERY
        load.transition_to(LoadState.DELIVERED)
        assert load.current_state == LoadState.DELIVERED

    def test_transition_to_invalid_state(self, sample_load):
        """Test that invalid state transitions raise errors."""
        load = Load(**sample_load)
        # Can't go from ON_ROUTE_TO_DELIVERY directly to DELIVERED
        with pytest.raises(InvalidStateTransitionError):
            load.transition_to(LoadState.DELIVERED)


class TestEvent:
    """Tests for Event domain models."""

    def test_create_inbound_communication_event(self, sample_inbound_communication):
        """Test creating an inbound communication event."""
        from src.domain.value_objects import InboundCommunication
        data = sample_inbound_communication
        inbound_comm = InboundCommunication(
            channel=data["event_data"]["channel"],
            sender_type=data["event_data"]["sender_type"],
            content=data["event_data"]["message"],
            attachments=data["event_data"]["attachments"],
        )
        event = InboundCommunicationEvent(
            event_id=data["event_id"],
            load_id=data["load_id"],
            customer_id=data["customer_id"],
            occurred_at=data["occurred_at"],
            inbound_communication=inbound_comm,
        )
        assert event.event_type == EventType.INBOUND_COMMUNICATION
        assert event.inbound_communication.sender_type == SenderType.DRIVER
        assert event.inbound_communication.channel == Channel.SMS

    def test_create_tracking_event(self, sample_tracking_event):
        """Test creating a tracking event."""
        from src.domain.value_objects import TrackingPing
        data = sample_tracking_event
        tracking = TrackingPing(
            tracking_id=f"trk-{uuid.uuid4()}",
            lat=data["event_data"]["latitude"],
            lng=data["event_data"]["longitude"],
            distance_to_delivery_miles=data["event_data"]["distance_to_delivery"],
            ping_sequence=1,
        )
        event = TrackingEvent(
            event_id=data["event_id"],
            load_id=data["load_id"],
            customer_id=data["customer_id"],
            occurred_at=data["occurred_at"],
            tracking=tracking,
        )
        assert event.event_type == EventType.TRACKING
        assert event.tracking.lat == 43.0389
        assert event.tracking.distance_to_delivery_miles == 5.2


class TestExceptions:
    """Tests for domain exceptions."""

    def test_load_not_found_error(self):
        """Test LoadNotFoundError."""
        error = LoadNotFoundError("load-123")
        assert "load-123" in str(error)

    def test_invalid_state_transition_error(self):
        """Test InvalidStateTransitionError."""
        error = InvalidStateTransitionError(
            from_state=LoadState.DISPATCHED,
            to_state=LoadState.DELIVERED,
        )
        assert "DISPATCHED" in str(error)
        assert "DELIVERED" in str(error)