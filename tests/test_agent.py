"""Tests for agent workflows."""

import uuid
from datetime import datetime, timezone

import pytest

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    SOPBranch,
    ConfirmDeliveryBranch,
    SenderType,
    Channel,
)
from src.agent.eta_checkpoint import create_eta_checkpoint_workflow
from src.agent.confirm_delivery import create_confirm_delivery_workflow


class TestETACheckpointWorkflow:
    """Tests for the ETA Checkpoint workflow."""

    @pytest.mark.asyncio
    async def test_workflow_creation(self):
        """Test that the ETA checkpoint workflow can be created."""
        workflow = create_eta_checkpoint_workflow()
        assert workflow is not None

    @pytest.mark.asyncio
    async def test_tracking_ping_classification(self):
        """Test that tracking pings are classified correctly."""
        workflow = create_eta_checkpoint_workflow()
        initial_state = {
            "event_id": f"evt-{uuid.uuid4()}",
            "load_id": f"load-{uuid.uuid4()}",
            "customer_id": "customer_a",
            "event_type": EventType.TRACKING.value,
            "event_data": {
                "latitude": 43.0389,
                "longitude": -87.9065,
                "distance_to_delivery": 5.2,
            },
            "load_data": {},
            "current_state": LoadState.ON_ROUTE_TO_DELIVERY.value,
            "current_eta_utc": "2024-01-15T13:30:00Z",
            "customer_config": {},
            "sop_content": "",
            "messages": [],
            "tool_calls": [],
            "memory_operations": [],
            "actions_taken": [],
        }

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}
        result = await workflow.ainvoke(initial_state, config)

        assert result.get("sop_branch") == SOPBranch.TRACKING_PING.value

    @pytest.mark.asyncio
    async def test_driver_eta_classification(self):
        """Test that driver ETA messages are classified correctly."""
        workflow = create_eta_checkpoint_workflow()
        initial_state = {
            "event_id": f"evt-{uuid.uuid4()}",
            "load_id": f"load-{uuid.uuid4()}",
            "customer_id": "customer_a",
            "event_type": EventType.INBOUND_COMMUNICATION.value,
            "event_data": {
                "sender_type": SenderType.DRIVER.value,
                "channel": Channel.SMS.value,
                "message": "I'll be there in about 30 minutes",
            },
            "load_data": {},
            "current_state": LoadState.ON_ROUTE_TO_DELIVERY.value,
            "current_eta_utc": "2024-01-15T13:30:00Z",
            "customer_config": {},
            "sop_content": "",
            "messages": [],
            "tool_calls": [],
            "memory_operations": [],
            "actions_taken": [],
        }

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}
        result = await workflow.ainvoke(initial_state, config)

        assert result.get("sop_branch") == SOPBranch.DRIVER_PROVIDES_ETA.value

    @pytest.mark.asyncio
    async def test_broker_message_classification(self):
        """Test that broker messages are classified correctly."""
        workflow = create_eta_checkpoint_workflow()
        initial_state = {
            "event_id": f"evt-{uuid.uuid4()}",
            "load_id": f"load-{uuid.uuid4()}",
            "customer_id": "customer_a",
            "event_type": EventType.INBOUND_COMMUNICATION.value,
            "event_data": {
                "sender_type": SenderType.BROKER.value,
                "channel": Channel.EMAIL.value,
                "message": "Update on load status",
            },
            "load_data": {},
            "current_state": LoadState.ON_ROUTE_TO_DELIVERY.value,
            "current_eta_utc": "2024-01-15T13:30:00Z",
            "customer_config": {},
            "sop_content": "",
            "messages": [],
            "tool_calls": [],
            "memory_operations": [],
            "actions_taken": [],
        }

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}
        result = await workflow.ainvoke(initial_state, config)

        assert result.get("sop_branch") == SOPBranch.BROKER_MESSAGES.value

    @pytest.mark.asyncio
    async def test_arrival_classification(self):
        """Test that arrival messages are classified correctly."""
        workflow = create_eta_checkpoint_workflow()
        initial_state = {
            "event_id": f"evt-{uuid.uuid4()}",
            "load_id": f"load-{uuid.uuid4()}",
            "customer_id": "customer_a",
            "event_type": EventType.INBOUND_COMMUNICATION.value,
            "event_data": {
                "sender_type": SenderType.DRIVER.value,
                "channel": Channel.SMS.value,
                "message": "I've arrived at the delivery location",
            },
            "load_data": {},
            "current_state": LoadState.ON_ROUTE_TO_DELIVERY.value,
            "current_eta_utc": "2024-01-15T13:30:00Z",
            "customer_config": {},
            "sop_content": "",
            "messages": [],
            "tool_calls": [],
            "memory_operations": [],
            "actions_taken": [],
        }

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}
        result = await workflow.ainvoke(initial_state, config)

        assert result.get("sop_branch") == SOPBranch.ARRIVAL_CONFIRMATION.value
        assert result.get("state_after") == LoadState.AT_DELIVERY.value


class TestConfirmDeliveryWorkflow:
    """Tests for the Confirm Delivery workflow."""

    @pytest.mark.asyncio
    async def test_workflow_creation(self):
        """Test that the confirm delivery workflow can be created."""
        workflow = create_confirm_delivery_workflow()
        assert workflow is not None

    @pytest.mark.asyncio
    async def test_pod_attachment_classification(self):
        """Test that POD attachments are classified correctly."""
        workflow = create_confirm_delivery_workflow()
        initial_state = {
            "event_id": f"evt-{uuid.uuid4()}",
            "load_id": f"load-{uuid.uuid4()}",
            "customer_id": "customer_a",
            "event_type": EventType.INBOUND_COMMUNICATION.value,
            "event_data": {
                "sender_type": SenderType.DRIVER.value,
                "channel": Channel.SMS.value,
                "message": "Here's the POD",
                "attachments": [
                    {
                        "url": "https://example.com/pod.pdf",
                        "classification": "pod",
                    }
                ],
            },
            "load_data": {},
            "current_state": LoadState.CONFIRM_DELIVERY.value,
            "customer_config": {},
            "sop_content": "",
            "messages": [],
            "tool_calls": [],
            "memory_operations": [],
            "actions_taken": [],
        }

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}
        result = await workflow.ainvoke(initial_state, config)

        assert result.get("sop_branch") == ConfirmDeliveryBranch.POD_DOCUMENT.value
        assert result.get("pod_received") is True

    @pytest.mark.asyncio
    async def test_delivery_confirmed_without_pod(self):
        """Test delivery confirmed without POD."""
        workflow = create_confirm_delivery_workflow()
        initial_state = {
            "event_id": f"evt-{uuid.uuid4()}",
            "load_id": f"load-{uuid.uuid4()}",
            "customer_id": "customer_a",
            "event_type": EventType.INBOUND_COMMUNICATION.value,
            "event_data": {
                "sender_type": SenderType.DRIVER.value,
                "channel": Channel.SMS.value,
                "message": "I'm unloaded and empty",
                "attachments": [],
            },
            "load_data": {},
            "current_state": LoadState.CONFIRM_DELIVERY.value,
            "customer_config": {},
            "sop_content": "",
            "messages": [],
            "tool_calls": [],
            "memory_operations": [],
            "actions_taken": [],
        }

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}
        result = await workflow.ainvoke(initial_state, config)

        assert result.get("sop_branch") == ConfirmDeliveryBranch.DELIVERED_WITHOUT_POD.value

    @pytest.mark.asyncio
    async def test_broker_message_no_action(self):
        """Test that broker messages result in no action."""
        workflow = create_confirm_delivery_workflow()
        initial_state = {
            "event_id": f"evt-{uuid.uuid4()}",
            "load_id": f"load-{uuid.uuid4()}",
            "customer_id": "customer_a",
            "event_type": EventType.INBOUND_COMMUNICATION.value,
            "event_data": {
                "sender_type": SenderType.BROKER.value,
                "channel": Channel.EMAIL.value,
                "message": "Status update from broker",
                "attachments": [],
            },
            "load_data": {},
            "current_state": LoadState.CONFIRM_DELIVERY.value,
            "customer_config": {},
            "sop_content": "",
            "messages": [],
            "tool_calls": [],
            "memory_operations": [],
            "actions_taken": [],
        }

        config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}
        result = await workflow.ainvoke(initial_state, config)

        assert result.get("sop_branch") == ConfirmDeliveryBranch.BROKER_MESSAGES.value