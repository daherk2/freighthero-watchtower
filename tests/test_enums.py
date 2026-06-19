"""Tests for domain enums."""

import pytest

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    Channel,
    SenderType,
    SOPBranch,
    ConfirmDeliveryBranch,
    MemoryType,
    MemoryScope,
    MemoryOperation,
    TimerType,
    TaskType,
    IssueType,
    AttachmentCategory,
)


class TestLoadState:
    """Tests for LoadState enum."""

    def test_state_values(self):
        """Test that all expected states exist."""
        assert LoadState.DISPATCHED.value == "dispatched"
        assert LoadState.ON_ROUTE_TO_DELIVERY.value == "on_route_to_delivery"
        assert LoadState.AT_DELIVERY.value == "at_delivery"
        assert LoadState.CONFIRM_DELIVERY.value == "confirm_delivery"
        assert LoadState.DELIVERED.value == "delivered"

    def test_state_from_string(self):
        """Test creating state from string."""
        assert LoadState("dispatched") == LoadState.DISPATCHED
        assert LoadState("delivered") == LoadState.DELIVERED


class TestCustomerId:
    """Tests for CustomerId enum."""

    def test_customer_values(self):
        """Test that all expected customer IDs exist."""
        assert CustomerId.CUSTOMER_A.value == "customer_a"
        assert CustomerId.CUSTOMER_B.value == "customer_b"
        assert CustomerId.CUSTOMER_C.value == "customer_c"


class TestEventType:
    """Tests for EventType enum."""

    def test_event_type_values(self):
        """Test that all expected event types exist."""
        assert EventType.INBOUND_COMMUNICATION.value == "inbound_communication"
        assert EventType.TRACKING.value == "tracking"
        assert EventType.LOAD_UPDATE.value == "load_update"
        assert EventType.TIMER_CALLBACK.value == "timer_callback"


class TestSOPBranch:
    """Tests for SOPBranch enum."""

    def test_eta_branches(self):
        """Test ETA checkpoint SOP branches."""
        assert SOPBranch.TRACKING_PING.value == "tracking_ping"
        assert SOPBranch.ARRIVAL_CONFIRMATION.value == "arrival_confirmation"
        assert SOPBranch.DRIVER_PROVIDES_ETA.value == "driver_provides_eta"
        assert SOPBranch.LOAD_INFORMATION_QUESTION.value == "load_information_question"
        assert SOPBranch.OPERATIONAL_ISSUE.value == "operational_issue"
        assert SOPBranch.BROKER_MESSAGES.value == "broker_messages"
        assert SOPBranch.NO_ACTION.value == "no_action"


class TestConfirmDeliveryBranch:
    """Tests for ConfirmDeliveryBranch enum."""

    def test_delivery_branches(self):
        """Test confirm delivery SOP branches."""
        assert ConfirmDeliveryBranch.POD_DOCUMENT.value == "pod_document"
        assert ConfirmDeliveryBranch.LUMPER_RECEIPT.value == "lumper_receipt"
        assert ConfirmDeliveryBranch.OTHER_ATTACHMENT.value == "other_attachment"
        assert ConfirmDeliveryBranch.UNLOADING_STARTED.value == "unloading_started"
        assert ConfirmDeliveryBranch.UNLOADING_NOT_STARTED.value == "unloading_not_started"
        assert ConfirmDeliveryBranch.DELIVERED_WITHOUT_POD.value == "delivered_without_pod"
        assert ConfirmDeliveryBranch.FIRST_ARRIVAL_CONTACT.value == "first_arrival_contact"
        assert ConfirmDeliveryBranch.OPERATIONAL_ISSUE.value == "operational_issue"
        assert ConfirmDeliveryBranch.BROKER_MESSAGES.value == "broker_messages"
        assert ConfirmDeliveryBranch.NO_ACTION.value == "no_action"


class TestMemoryEnums:
    """Tests for memory-related enums."""

    def test_memory_type_values(self):
        """Test MemoryType enum values."""
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.PROCEDURAL.value == "procedural"

    def test_memory_scope_values(self):
        """Test MemoryScope enum values."""
        assert MemoryScope.LOAD.value == "load"
        assert MemoryScope.CUSTOMER.value == "customer"
        assert MemoryScope.GLOBAL.value == "global"

    def test_memory_operation_values(self):
        """Test MemoryOperation enum values."""
        assert MemoryOperation.ADD.value == "add"
        assert MemoryOperation.RETRIEVE.value == "retrieve"
        assert MemoryOperation.UPDATE.value == "update"
        assert MemoryOperation.DELETE.value == "delete"
        assert MemoryOperation.SUMMARIZE.value == "summarize"
        assert MemoryOperation.FILTER.value == "filter"