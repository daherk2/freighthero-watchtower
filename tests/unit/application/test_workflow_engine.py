"""Tests for WorkflowEngine service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.application.services.workflow_engine import WorkflowEngine
from src.domain.enums import CustomerId, EventType, LoadState, SOPBranch
from src.domain.exceptions import LoadNotFoundError
from src.domain.models import Event, Load, AgentRun
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
    return Event(
        event_id="evt-1",
        event_type=EventType.INBOUND_COMMUNICATION,
        load_id="load-1",
        customer_id=CustomerId.CUSTOMER_A,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        event_data={"message": "ETA in 30 min"},
    )


@pytest.fixture
def sample_agent_run():
    return AgentRun(
        run_id="run-1",
        event_id="evt-1",
        load_id="load-1",
        customer_id=CustomerId.CUSTOMER_A,
        workflow="delivery_eta_checkpoint",
        sop_branch=SOPBranch.DRIVER_PROVIDES_ETA,
        customer_rules_applied=["escalation_channel"],
        tool_calls=[],
        memory_operations=[],
        state_before=LoadState.DISPATCHED,
        state_after=LoadState.ON_ROUTE_TO_DELIVERY,
        status="completed",
        started_at=datetime.now(timezone.utc).isoformat(),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


class TestWorkflowEngineInit:
    def test_init_with_all_deps(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, mock_memory_repo, mock_tool_call_repo, mock_customer_resolver, mock_sop_compiler):
        engine = WorkflowEngine(
            load_repo=mock_load_repo, event_repo=mock_event_repo,
            agent_run_repo=mock_agent_run_repo, memory_repo=mock_memory_repo,
            tool_call_repo=mock_tool_call_repo, customer_resolver=mock_customer_resolver,
            sop_compiler=mock_sop_compiler,
        )
        assert engine._load_repo is mock_load_repo
        assert engine._memory_repo is mock_memory_repo

    def test_init_with_defaults(self, mock_load_repo, mock_event_repo, mock_agent_run_repo):
        engine = WorkflowEngine(
            load_repo=mock_load_repo, event_repo=mock_event_repo,
            agent_run_repo=mock_agent_run_repo,
        )
        assert engine._memory_repo is None
        assert engine._tool_call_repo is None
        assert engine._customer_resolver is not None
        assert engine._sop_compiler is not None


class TestWorkflowEngineExecute:
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, mock_customer_resolver, mock_sop_compiler, sample_load, sample_event, sample_agent_run):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_agent_run_repo.save = AsyncMock(return_value=sample_agent_run)
        mock_agent_run_repo.update_status = AsyncMock()

        with patch("src.agent.orchestrator.AgentOrchestrator") as MockOrchestrator:
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator_instance.run = AsyncMock(return_value={
                "sop_branch": "driver_provides_eta",
                "customer_rules_applied": ["escalation_channel"],
                "tool_calls": [],
                "memory_operations": [],
                "state_after": "on_route_to_delivery",
            })
            MockOrchestrator.return_value = mock_orchestrator_instance

            engine = WorkflowEngine(
                load_repo=mock_load_repo, event_repo=mock_event_repo,
                agent_run_repo=mock_agent_run_repo, customer_resolver=mock_customer_resolver,
                sop_compiler=mock_sop_compiler,
            )
            result = await engine.execute("evt-1", "load-1", "delivery_eta_checkpoint")
            assert result.status == "completed"
            mock_agent_run_repo.save.assert_called_once()
            mock_agent_run_repo.update_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_failure_updates_status(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, mock_customer_resolver, mock_sop_compiler, sample_load, sample_event):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_agent_run_repo.save = AsyncMock()
        mock_agent_run_repo.update_status = AsyncMock()

        with patch("src.agent.orchestrator.AgentOrchestrator") as MockOrchestrator:
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator_instance.run = AsyncMock(side_effect=RuntimeError("Workflow failed"))
            MockOrchestrator.return_value = mock_orchestrator_instance

            engine = WorkflowEngine(
                load_repo=mock_load_repo, event_repo=mock_event_repo,
                agent_run_repo=mock_agent_run_repo, customer_resolver=mock_customer_resolver,
                sop_compiler=mock_sop_compiler,
            )
            with pytest.raises(RuntimeError, match="Workflow failed"):
                await engine.execute("evt-1", "load-1", "delivery_eta_checkpoint")
            mock_agent_run_repo.update_status.assert_called_once()


class TestWorkflowEngineGetRun:
    @pytest.mark.asyncio
    async def test_get_run(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, sample_agent_run):
        mock_agent_run_repo.get_by_id = AsyncMock(return_value=sample_agent_run)

        engine = WorkflowEngine(load_repo=mock_load_repo, event_repo=mock_event_repo, agent_run_repo=mock_agent_run_repo)
        result = await engine.get_run("run-1")
        assert result.run_id == "run-1"


class TestWorkflowEngineGetRunsForLoad:
    @pytest.mark.asyncio
    async def test_get_runs_for_load(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, sample_agent_run):
        mock_agent_run_repo.get_by_load_id = AsyncMock(return_value=[sample_agent_run])

        engine = WorkflowEngine(load_repo=mock_load_repo, event_repo=mock_event_repo, agent_run_repo=mock_agent_run_repo)
        result = await engine.get_runs_for_load("load-1")
        assert len(result) == 1