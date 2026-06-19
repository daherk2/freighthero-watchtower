"""Tests for AgentOrchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.agent.orchestrator import AgentOrchestrator
from src.domain.enums import CustomerId, EventType, LoadState, SOPBranch
from src.domain.models import Event, Load
from src.domain.value_objects import CustomerBehaviorConfig


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


def make_customer_config(**overrides):
    defaults = dict(
        customer_id=CustomerId.CUSTOMER_A,
        escalation_channel="email",
        missing_load_info_action="create_task",
        pod_validation_type="automated",
        pod_received_visibility="notify_escalation_channel",
        delivered_without_pod_visibility="notify_escalation_channel",
        delivery_geofence_radius_miles=5,
        eta_followup_timer_minutes=30,
        lumper_receipt_handling="classify_and_create_review_task",
        first_arrival_message="Driver has arrived",
    )
    defaults.update(overrides)
    return CustomerBehaviorConfig(**defaults)


@pytest.fixture
def mock_load_repo():
    return AsyncMock()


@pytest.fixture
def mock_event_repo():
    return AsyncMock()


@pytest.fixture
def mock_agent_run_repo():
    return AsyncMock()


@pytest.fixture
def mock_memory_repo():
    return AsyncMock()


@pytest.fixture
def mock_tool_call_repo():
    return AsyncMock()


@pytest.fixture
def mock_customer_resolver():
    resolver = AsyncMock()
    config = make_customer_config()
    resolver.get_config = AsyncMock(return_value=config)
    return resolver


@pytest.fixture
def mock_sop_compiler():
    compiler = AsyncMock()
    compiler.get_sop = AsyncMock(return_value="SOP content for delivery_eta_checkpoint")
    return compiler


@pytest.fixture
def sample_load():
    return make_load()


@pytest.fixture
def sample_event():
    return make_event()


class TestAgentOrchestratorInit:
    def test_init_with_all_deps(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, mock_memory_repo, mock_tool_call_repo, mock_customer_resolver, mock_sop_compiler):
        with patch("src.agent.orchestrator.create_eta_checkpoint_workflow") as mock_eta, \
             patch("src.agent.orchestrator.create_confirm_delivery_workflow") as mock_confirm:
            mock_eta.return_value = MagicMock()
            mock_confirm.return_value = MagicMock()

            orchestrator = AgentOrchestrator(
                load_repo=mock_load_repo, event_repo=mock_event_repo,
                agent_run_repo=mock_agent_run_repo, memory_repo=mock_memory_repo,
                tool_call_repo=mock_tool_call_repo, customer_resolver=mock_customer_resolver,
                sop_compiler=mock_sop_compiler,
            )
            assert orchestrator._load_repo is mock_load_repo
            assert orchestrator._memory_repo is mock_memory_repo
            assert "delivery_eta_checkpoint" in orchestrator._workflows
            assert "confirm_delivery" in orchestrator._workflows

    def test_init_with_defaults(self, mock_load_repo, mock_event_repo, mock_agent_run_repo):
        with patch("src.agent.orchestrator.create_eta_checkpoint_workflow") as mock_eta, \
             patch("src.agent.orchestrator.create_confirm_delivery_workflow") as mock_confirm:
            mock_eta.return_value = MagicMock()
            mock_confirm.return_value = MagicMock()

            orchestrator = AgentOrchestrator(
                load_repo=mock_load_repo, event_repo=mock_event_repo,
                agent_run_repo=mock_agent_run_repo,
            )
            assert orchestrator._customer_resolver is not None
            assert orchestrator._sop_compiler is not None


class TestAgentOrchestratorRun:
    @pytest.mark.asyncio
    async def test_run_success(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, mock_memory_repo, mock_tool_call_repo, mock_customer_resolver, mock_sop_compiler, sample_load, sample_event):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_agent_run_repo.save = AsyncMock()

        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(return_value={
            "sop_branch": "driver_provides_eta",
            "branch_reason": "Driver provided ETA",
            "tool_calls": [{"tool": "send_sms", "arguments": {}, "result": {}}],
            "memory_operations": [],
            "state_after": "on_route_to_delivery",
            "actions_taken": ["sent_sms"],
        })

        with patch("src.agent.orchestrator.create_eta_checkpoint_workflow", return_value=mock_workflow), \
             patch("src.agent.orchestrator.create_confirm_delivery_workflow", return_value=mock_workflow):
            orchestrator = AgentOrchestrator(
                load_repo=mock_load_repo, event_repo=mock_event_repo,
                agent_run_repo=mock_agent_run_repo, memory_repo=mock_memory_repo,
                tool_call_repo=mock_tool_call_repo, customer_resolver=mock_customer_resolver,
                sop_compiler=mock_sop_compiler,
            )
            result = await orchestrator.run("evt-1", "load-1", "delivery_eta_checkpoint")
            assert result["status"] == "completed"
            assert result["workflow"] == "delivery_eta_checkpoint"
            assert result["event_id"] == "evt-1"
            assert result["load_id"] == "load-1"

    @pytest.mark.asyncio
    async def test_run_unknown_workflow(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, mock_customer_resolver, mock_sop_compiler, sample_load, sample_event):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)

        mock_workflow = AsyncMock()
        with patch("src.agent.orchestrator.create_eta_checkpoint_workflow", return_value=mock_workflow), \
             patch("src.agent.orchestrator.create_confirm_delivery_workflow", return_value=mock_workflow):
            orchestrator = AgentOrchestrator(
                load_repo=mock_load_repo, event_repo=mock_event_repo,
                agent_run_repo=mock_agent_run_repo, customer_resolver=mock_customer_resolver,
                sop_compiler=mock_sop_compiler,
            )
            with pytest.raises(ValueError, match="Unknown workflow"):
                await orchestrator.run("evt-1", "load-1", "unknown_workflow")

    @pytest.mark.asyncio
    async def test_run_without_agent_run_repo(self, mock_load_repo, mock_event_repo, mock_memory_repo, mock_customer_resolver, mock_sop_compiler, sample_load, sample_event):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)

        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(return_value={
            "sop_branch": "driver_provides_eta",
            "tool_calls": [],
            "memory_operations": [],
            "state_after": "on_route_to_delivery",
        })

        with patch("src.agent.orchestrator.create_eta_checkpoint_workflow", return_value=mock_workflow), \
             patch("src.agent.orchestrator.create_confirm_delivery_workflow", return_value=mock_workflow):
            orchestrator = AgentOrchestrator(
                load_repo=mock_load_repo, event_repo=mock_event_repo,
                agent_run_repo=None, memory_repo=mock_memory_repo,
                customer_resolver=mock_customer_resolver, sop_compiler=mock_sop_compiler,
            )
            result = await orchestrator.run("evt-1", "load-1", "delivery_eta_checkpoint")
            assert result["status"] == "completed"


class TestAgentOrchestratorGetWorkflow:
    @pytest.mark.asyncio
    async def test_get_workflow(self, mock_load_repo, mock_event_repo, mock_agent_run_repo):
        mock_workflow = MagicMock()
        with patch("src.agent.orchestrator.create_eta_checkpoint_workflow", return_value=mock_workflow), \
             patch("src.agent.orchestrator.create_confirm_delivery_workflow", return_value=mock_workflow):
            orchestrator = AgentOrchestrator(
                load_repo=mock_load_repo, event_repo=mock_event_repo,
                agent_run_repo=mock_agent_run_repo,
            )
            result = await orchestrator.get_workflow("delivery_eta_checkpoint")
            assert result is mock_workflow

    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, mock_load_repo, mock_event_repo, mock_agent_run_repo):
        mock_workflow = MagicMock()
        with patch("src.agent.orchestrator.create_eta_checkpoint_workflow", return_value=mock_workflow), \
             patch("src.agent.orchestrator.create_confirm_delivery_workflow", return_value=mock_workflow):
            orchestrator = AgentOrchestrator(
                load_repo=mock_load_repo, event_repo=mock_event_repo,
                agent_run_repo=mock_agent_run_repo,
            )
            result = await orchestrator.get_workflow("nonexistent")
            assert result is None