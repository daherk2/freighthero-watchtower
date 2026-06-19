"""Tests for agent tools."""

import pytest

from src.agent.tools import (
    # Communication tools
    send_sms,
    send_email,
    forward_email,
    send_slack_message,
    # Attachment tools
    check_attachment,
    # Load state tools
    update_load_state,
    update_eta,
    # Timer tools
    create_timer,
    cancel_timer,
    cancel_timers,
    # Human work tools
    create_task,
    create_issue,
    # Helper tools
    get_load_info,
    validate_eta,
    get_appointment_time,
    # Internal tools
    record_sop_branch,
    no_action,
    get_geofence_status,
    # Memory tools
    memory_add,
    memory_retrieve,
    memory_update,
    memory_delete,
    memory_summarize,
    memory_filter,
    # Registries
    ALL_TOOLS,
    MOCK_TOOLS,
    MEMORY_TOOLS,
    COMMUNICATION_TOOLS,
)


class TestCommunicationTools:
    """Tests for communication tools."""

    @pytest.mark.asyncio
    async def test_send_sms(self):
        """Test send_sms tool."""
        result = await send_sms.ainvoke({
            "recipient": "driver",
            "message": "Test SMS message",
        })
        assert result["ok"] is True
        assert result["channel"] == "sms"
        assert "sms-" in result["message_id"]

    @pytest.mark.asyncio
    async def test_send_email(self):
        """Test send_email tool."""
        result = await send_email.ainvoke({
            "recipient": "dispatcher",
            "subject": "Load Update",
            "body": "Test email body",
        })
        assert result["ok"] is True
        assert result["channel"] == "email"
        assert "email-" in result["message_id"]

    @pytest.mark.asyncio
    async def test_forward_email(self):
        """Test forward_email tool."""
        result = await forward_email.ainvoke({})
        assert result["ok"] is True
        assert result["channel"] == "email"
        assert "fwd-" in result["message_id"]

    @pytest.mark.asyncio
    async def test_send_slack_message(self):
        """Test send_slack_message tool."""
        result = await send_slack_message.ainvoke({
            "audience": "internal",
            "message": "Test Slack message",
        })
        assert result["ok"] is True
        assert result["channel"] == "slack"
        assert "slack-" in result["message_id"]

    @pytest.mark.asyncio
    async def test_send_slack_message_with_escalation(self):
        """Test send_slack_message tool with escalation type."""
        result = await send_slack_message.ainvoke({
            "audience": "broker",
            "message": "Test escalation",
            "escalation_type": "equipment_failure",
        })
        assert result["ok"] is True
        assert result["escalation_type"] == "equipment_failure"


class TestAttachmentTools:
    """Tests for attachment tools."""

    @pytest.mark.asyncio
    async def test_check_attachment(self):
        """Test check_attachment tool."""
        result = await check_attachment.ainvoke({
            "attachment_id": "att-pod-1",
        })
        assert result["ok"] is True
        assert result["attachment_id"] == "att-pod-1"
        assert "categories" in result


class TestLoadStateTools:
    """Tests for load state tools."""

    @pytest.mark.asyncio
    async def test_update_load_state(self):
        """Test update_load_state tool with target_state."""
        result = await update_load_state.ainvoke({
            "target_state": "at_delivery",
            "reason": "Driver arrived",
        })
        assert result["ok"] is True
        assert result["new_state"] == "at_delivery"

    @pytest.mark.asyncio
    async def test_update_eta(self):
        """Test update_eta tool."""
        result = await update_eta.ainvoke({
            "target_location": "delivery",
            "eta_utc": "2026-05-11T19:30:00Z",
            "source": "driver",
        })
        assert result["ok"] is True
        assert result["target_location"] == "delivery"
        assert result["source"] == "driver"


class TestTimerTools:
    """Tests for timer tools."""

    @pytest.mark.asyncio
    async def test_create_timer(self):
        """Test create_timer tool."""
        result = await create_timer.ainvoke({
            "timer_type": "eta_followup",
            "fire_at_utc": "2026-05-11T20:00:00Z",
            "reason": "ETA follow-up",
        })
        assert result["ok"] is True
        assert result["timer_type"] == "eta_followup"
        assert "timer-" in result["timer_id"]

    @pytest.mark.asyncio
    async def test_cancel_timer(self):
        """Test cancel_timer tool."""
        result = await cancel_timer.ainvoke({
            "timer_id": "timer-001",
        })
        assert result["ok"] is True
        assert result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_timers(self):
        """Test cancel_timers tool."""
        result = await cancel_timers.ainvoke({
            "timer_type": "eta_followup",
        })
        assert result["ok"] is True
        assert result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_all_timers(self):
        """Test cancel_timers tool with no timer_type (cancel all)."""
        result = await cancel_timers.ainvoke({})
        assert result["ok"] is True


class TestHumanWorkTools:
    """Tests for human work tools."""

    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test create_task tool."""
        result = await create_task.ainvoke({
            "title": "Missing load info",
            "description": "Driver requested missing load information",
            "task_type": "missing_load_info",
        })
        assert result["ok"] is True
        assert "task-" in result["task_id"]
        assert result["task_type"] == "missing_load_info"

    @pytest.mark.asyncio
    async def test_create_issue(self):
        """Test create_issue tool."""
        result = await create_issue.ainvoke({
            "title": "Truck breakdown",
            "description": "Driver reports truck broke down",
            "issue_type": "equipment_failure",
        })
        assert result["ok"] is True
        assert "issue-" in result["issue_id"]
        assert result["issue_type"] == "equipment_failure"


class TestHelperTools:
    """Tests for helper tools."""

    @pytest.mark.asyncio
    async def test_get_load_info(self):
        """Test get_load_info tool with field parameter."""
        result = await get_load_info.ainvoke({
            "field": "delivery_address",
        })
        assert result["ok"] is True
        assert result["field"] == "delivery_address"

    @pytest.mark.asyncio
    async def test_validate_eta(self):
        """Test validate_eta tool."""
        result = await validate_eta.ainvoke({
            "raw_eta": "3pm",
            "delivery_timezone": "America/Chicago",
        })
        assert result["ok"] is True
        assert "eta_utc" in result
        assert "is_plausible" in result

    @pytest.mark.asyncio
    async def test_get_appointment_time(self):
        """Test get_appointment_time tool."""
        result = await get_appointment_time.ainvoke({
            "stop_type": "delivery",
        })
        assert result["ok"] is True
        assert result["stop_type"] == "delivery"
        assert "appointment" in result


class TestInternalTools:
    """Tests for internal tools."""

    @pytest.mark.asyncio
    async def test_record_sop_branch(self):
        """Test record_sop_branch tool."""
        result = await record_sop_branch.ainvoke({
            "load_id": "load-001",
            "event_id": "evt-001",
            "branch": "arrival_confirmation",
            "reason": "Driver arrived at delivery",
        })
        assert result["branch"] == "arrival_confirmation"

    @pytest.mark.asyncio
    async def test_no_action(self):
        """Test no_action tool."""
        result = await no_action.ainvoke({
            "load_id": "load-001",
            "event_id": "evt-001",
            "reason": "Broker message - no action per SOP",
        })
        assert result["action"] == "none"

    @pytest.mark.asyncio
    async def test_get_geofence_status(self):
        """Test get_geofence_status tool."""
        result = await get_geofence_status.ainvoke({
            "load_id": "load-001",
            "latitude": 43.0389,
            "longitude": -87.9065,
        })
        assert "within_geofence" in result
        assert "distance_miles" in result


class TestMemoryTools:
    """Tests for memory tools."""

    @pytest.mark.asyncio
    async def test_memory_add(self):
        """Test memory_add tool."""
        result = await memory_add.ainvoke({
            "memory_type": "episodic",
            "scope": "load",
            "scope_id": "load-001",
            "content": "Driver arrived at delivery",
        })
        assert result["status"] == "added"
        assert result["memory_id"] is not None

    @pytest.mark.asyncio
    async def test_memory_retrieve(self):
        """Test memory_retrieve tool."""
        result = await memory_retrieve.ainvoke({
            "scope": "load",
            "scope_id": "load-001",
        })
        assert "memories" in result
        assert result["scope"] == "load"

    @pytest.mark.asyncio
    async def test_memory_update(self):
        """Test memory_update tool."""
        result = await memory_update.ainvoke({
            "memory_id": "mem-001",
            "content": "Updated content",
        })
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_memory_delete(self):
        """Test memory_delete tool."""
        result = await memory_delete.ainvoke({"memory_id": "mem-001"})
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_memory_summarize(self):
        """Test memory_summarize tool."""
        result = await memory_summarize.ainvoke({
            "scope": "load",
            "scope_id": "load-001",
            "memory_type": "episodic",
        })
        assert result["status"] == "summarized"

    @pytest.mark.asyncio
    async def test_memory_filter(self):
        """Test memory_filter tool."""
        result = await memory_filter.ainvoke({
            "scope": "load",
            "scope_id": "load-001",
            "memory_type": "episodic",
            "relevance_threshold": 0.5,
        })
        assert result["status"] == "filtered"


class TestToolRegistry:
    """Tests for the tool registry."""

    def test_all_tools_count(self):
        """Test that all tools are registered."""
        # 4 comm + 1 attachment + 2 load state + 3 timer + 2 human work
        # + 3 helper + 3 internal + 6 memory = 24
        assert len(ALL_TOOLS) == 24

    def test_mock_tools_count(self):
        """Test that mock tools are registered."""
        # 4 comm + 1 attachment + 2 load state + 3 timer + 2 human work
        # + 3 helper + 3 internal = 18
        assert len(MOCK_TOOLS) == 18

    def test_memory_tools_count(self):
        """Test that memory tools are registered."""
        assert len(MEMORY_TOOLS) == 6

    def test_communication_tools_count(self):
        """Test that communication tools are registered."""
        assert len(COMMUNICATION_TOOLS) == 4

    def test_tool_names(self):
        """Test that all tools have unique names."""
        names = [t.name for t in ALL_TOOLS]
        assert len(names) == len(set(names))

    def test_spec_tool_names_present(self):
        """Test that all spec-required tool names are present."""
        spec_tools = [
            "send_sms", "send_email", "forward_email", "send_slack_message",
            "check_attachment", "update_load_state", "update_eta",
            "create_timer", "cancel_timer", "cancel_timers",
            "create_task", "create_issue",
            "get_load_info", "validate_eta", "get_appointment_time",
        ]
        all_names = [t.name for t in ALL_TOOLS]
        for tool_name in spec_tools:
            assert tool_name in all_names, f"Missing spec tool: {tool_name}"
