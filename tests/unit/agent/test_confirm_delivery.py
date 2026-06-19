"""Tests for the Confirm Delivery LangGraph workflow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.domain.enums import (
    CustomerId, EventType, LoadState, ConfirmDeliveryBranch, SenderType,
)
from src.agent.confirm_delivery import (
    ConfirmDeliveryState,
    create_confirm_delivery_workflow,
)


class TestConfirmDeliveryWorkflowCreation:
    """Tests for workflow creation."""

    def test_create_workflow_returns_compiled_graph(self):
        """Test that create_confirm_delivery_workflow returns a compiled graph."""
        workflow = create_confirm_delivery_workflow()
        assert workflow is not None

    def test_create_workflow_with_llm(self):
        """Test that workflow can be created with an LLM."""
        mock_llm = MagicMock()
        workflow = create_confirm_delivery_workflow(llm=mock_llm)
        assert workflow is not None

    def test_create_workflow_with_tools(self):
        """Test that workflow can be created with tools."""
        mock_tools = [MagicMock()]
        workflow = create_confirm_delivery_workflow(tools=mock_tools)
        assert workflow is not None


class TestConfirmDeliveryClassifyEvent:
    """Tests for the classify_event node logic."""

    @pytest.mark.asyncio
    async def test_classify_broker_message(self):
        """Test that broker messages are classified correctly via workflow."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-broker-classify"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-broker-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={"sender_type": SenderType.BROKER.value, "message": "Checking on load status"},
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={},
            sop_content="",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.BROKER_MESSAGES.value

    def test_confirm_delivery_branch_values(self):
        """Test that all ConfirmDeliveryBranch values exist."""
        assert ConfirmDeliveryBranch.POD_DOCUMENT.value == "pod_document"
        assert ConfirmDeliveryBranch.LUMPER_RECEIPT.value == "lumper_receipt"
        assert ConfirmDeliveryBranch.DELIVERED_WITHOUT_POD.value == "delivered_without_pod"
        assert ConfirmDeliveryBranch.UNLOADING_STARTED.value == "unloading_started"
        assert ConfirmDeliveryBranch.UNLOADING_NOT_STARTED.value == "unloading_not_started"
        assert ConfirmDeliveryBranch.OPERATIONAL_ISSUE.value == "operational_issue"
        assert ConfirmDeliveryBranch.BROKER_MESSAGES.value == "broker_messages"
        assert ConfirmDeliveryBranch.FIRST_ARRIVAL_CONTACT.value == "first_arrival_contact"
        assert ConfirmDeliveryBranch.NO_ACTION.value == "no_action"
        assert ConfirmDeliveryBranch.OTHER_ATTACHMENT.value == "other_attachment"


class TestConfirmDeliveryWorkflowInvocation:
    """Tests for invoking the confirm delivery workflow."""

    @pytest.mark.asyncio
    async def test_workflow_with_pod_attachment(self):
        """Test workflow with POD document attachment."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-pod-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-pod-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "attachments": [{
                    "attachment_id": "att-1",
                    "classification": "pod",
                    "url": "https://example.com/pod.pdf",
                    "file_name": "pod.pdf",
                }],
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "pod_validation_type": "automatic",
                "pod_received_visibility": "internal",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.POD_DOCUMENT.value
        assert result.get("pod_received") is True

    @pytest.mark.asyncio
    async def test_workflow_with_lumper_attachment(self):
        """Test workflow with lumper receipt attachment."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-lumper-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-lumper-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "attachments": [{
                    "attachment_id": "att-2",
                    "classification": "lumper_receipt",
                    "url": "https://example.com/lumper.pdf",
                    "file_name": "lumper_receipt.pdf",
                }],
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "lumper_receipt_handling": "classify_and_create_review_task",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.LUMPER_RECEIPT.value
        assert result.get("lumper_received") is True

    @pytest.mark.asyncio
    async def test_workflow_with_broker_message(self):
        """Test workflow with broker message."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-broker-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-broker-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "sender_type": SenderType.BROKER.value,
                "message": "Checking on load status",
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={},
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.BROKER_MESSAGES.value

    @pytest.mark.asyncio
    async def test_workflow_with_delivered_message(self):
        """Test workflow with driver confirming delivery without POD."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-delivered-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-delivered-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "message": "I've unloaded and I'm done",
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "delivered_without_pod_visibility": "notify_escalation_channel",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.DELIVERED_WITHOUT_POD.value

    @pytest.mark.asyncio
    async def test_workflow_with_unloading_started(self):
        """Test workflow with driver reporting unloading started."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-unloading-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-unloading-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "message": "Started unloading at the facility",
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={},
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.UNLOADING_STARTED.value

    @pytest.mark.asyncio
    async def test_workflow_with_operational_issue(self):
        """Test workflow with driver reporting an operational issue."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-issue-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-issue-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "message": "There's a problem at the delivery site, I'm stuck",
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.OPERATIONAL_ISSUE.value

    @pytest.mark.asyncio
    async def test_workflow_with_tracking_event(self):
        """Test workflow with tracking event (first arrival contact)."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-tracking-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-tracking-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.TRACKING.value,
            event_data={
                "latitude": 32.7767,
                "longitude": -96.7970,
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={},
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.FIRST_ARRIVAL_CONTACT.value

    @pytest.mark.asyncio
    async def test_workflow_no_action(self):
        """Test workflow with no specific action needed."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-noaction-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-noaction-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "message": "Just checking in",
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={},
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.NO_ACTION.value

    @pytest.mark.asyncio
    async def test_workflow_with_mock_classification_pod(self):
        """Test workflow with attachment that has mock_classification for POD."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-mock-pod-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-mock-pod-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "attachments": [{
                    "attachment_id": "att-3",
                    "classification": "unknown",
                    "url": "https://example.com/doc.pdf",
                    "file_name": "delivery_receipt.pdf",
                    "mock_classification": {
                        "categories": ["document_pod"],
                        "description": "Proof of delivery document",
                    },
                }],
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "pod_validation_type": "automatic",
                "pod_received_visibility": "internal",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.POD_DOCUMENT.value
        assert result.get("pod_received") is True

    @pytest.mark.asyncio
    async def test_workflow_with_mock_classification_lumper(self):
        """Test workflow with attachment that has mock_classification for lumper."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-mock-lumper-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-mock-lumper-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "attachments": [{
                    "attachment_id": "att-4",
                    "classification": "unknown",
                    "url": "https://example.com/lumper.pdf",
                    "file_name": "lumper_receipt.pdf",
                    "mock_classification": {
                        "categories": ["lumper_receipt"],
                        "description": "Lumper receipt for unloading",
                    },
                }],
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "lumper_receipt_handling": "classify_and_create_review_task",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.LUMPER_RECEIPT.value
        assert result.get("lumper_received") is True

    @pytest.mark.asyncio
    async def test_workflow_pod_with_human_review(self):
        """Test workflow with POD that requires human review."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-human-review-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-human-review-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "attachments": [{
                    "attachment_id": "att-5",
                    "classification": "pod",
                    "url": "https://example.com/pod.pdf",
                    "file_name": "pod.pdf",
                }],
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "pod_validation_type": "human_review",
                "pod_received_visibility": "internal",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.POD_DOCUMENT.value
        # Check that human review task was created
        tool_calls = result.get("tool_calls", [])
        tool_names = [tc.get("tool") for tc in tool_calls]
        assert "create_task" in tool_names

    @pytest.mark.asyncio
    async def test_workflow_pod_with_notify_escalation(self):
        """Test workflow with POD that notifies escalation channel."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-notify-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-notify-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "attachments": [{
                    "attachment_id": "att-6",
                    "classification": "pod",
                    "url": "https://example.com/pod.pdf",
                    "file_name": "pod.pdf",
                }],
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "pod_validation_type": "automatic",
                "pod_received_visibility": "notify_escalation_channel",
                "escalation_channel": "email_and_slack",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.POD_DOCUMENT.value
        tool_calls = result.get("tool_calls", [])
        tool_names = [tc.get("tool") for tc in tool_calls]
        assert "send_email" in tool_names
        assert "send_slack_message" in tool_names

    @pytest.mark.asyncio
    async def test_workflow_lumper_forward_email(self):
        """Test workflow with lumper receipt forwarded via email."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-lumper-email-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-lumper-email-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "attachments": [{
                    "attachment_id": "att-7",
                    "classification": "lumper_receipt",
                    "url": "https://example.com/lumper.pdf",
                    "file_name": "lumper_receipt.pdf",
                }],
                "channel": "email",
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "lumper_receipt_handling": "forward_email_if_lumper_else_review_task",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.LUMPER_RECEIPT.value
        tool_calls = result.get("tool_calls", [])
        tool_names = [tc.get("tool") for tc in tool_calls]
        assert "forward_email" in tool_names

    @pytest.mark.asyncio
    async def test_workflow_state_transition_pod_collected(self):
        """Test that POD branch transitions to pod_collected state."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-state-pod-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-state-pod-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "attachments": [{
                    "attachment_id": "att-8",
                    "classification": "pod",
                    "url": "https://example.com/pod.pdf",
                    "file_name": "pod.pdf",
                }],
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "pod_validation_type": "automatic",
                "pod_received_visibility": "internal",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("state_after") == LoadState.POD_COLLECTED.value
        assert result.get("pod_status") == "collected"

    @pytest.mark.asyncio
    async def test_workflow_state_transition_delivered_without_pod(self):
        """Test that delivered_without_pod branch transitions to confirm_delivery state."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-state-del-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-state-del-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "message": "I've delivered the load",
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "delivered_without_pod_visibility": "no_notification",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("state_after") == LoadState.CONFIRM_DELIVERY.value
        assert result.get("pod_status") == "pending"

    @pytest.mark.asyncio
    async def test_workflow_other_attachment(self):
        """Test workflow with unrecognized attachment type."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-other-att-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-other-att-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "attachments": [{
                    "attachment_id": "att-9",
                    "classification": "invoice",
                    "url": "https://example.com/invoice.pdf",
                    "file_name": "invoice.pdf",
                }],
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={},
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.OTHER_ATTACHMENT.value

    @pytest.mark.asyncio
    async def test_workflow_unloading_not_started(self):
        """Test workflow with driver reporting unloading not started."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-not-started-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-not-started-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "message": "waiting to unload at the dock",
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={},
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=False,
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        assert result.get("sop_branch") == ConfirmDeliveryBranch.UNLOADING_NOT_STARTED.value

    @pytest.mark.asyncio
    async def test_workflow_delivered_with_pod_already_received(self):
        """Test workflow where driver confirms delivery - goes to delivered_without_pod since load_context resets pod_received."""
        workflow = create_confirm_delivery_workflow()
        config = {"configurable": {"thread_id": "test-pod-already-1"}}
        initial_state = ConfirmDeliveryState(
            event_id="evt-pod-already-1",
            load_id="load-1",
            customer_id="customer_a",
            event_type=EventType.INBOUND_COMMUNICATION.value,
            event_data={
                "message": "I'm done, unloaded everything",
            },
            load_data={},
            current_state=LoadState.AT_DELIVERY.value,
            customer_config={
                "delivered_without_pod_visibility": "notify_escalation_channel",
                "escalation_channel": "email",
            },
            sop_content="SOP for confirm delivery",
            sop_branch="",
            branch_reason="",
            attachment_classifications=[],
            pod_received=True,  # This gets reset to False by load_context node
            lumper_received=False,
            messages=[],
            tool_calls=[],
            memory_operations=[],
            state_after=None,
            actions_taken=[],
            followup_scheduled=False,
            escalation_sent=False,
            pod_status="pending",
        )
        result = await workflow.ainvoke(initial_state, config)
        # load_context resets pod_received to False, so this goes to delivered_without_pod
        assert result.get("sop_branch") == ConfirmDeliveryBranch.DELIVERED_WITHOUT_POD.value