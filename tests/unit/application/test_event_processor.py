"""Tests for EventProcessor service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.application.services.event_processor import EventProcessor
from src.domain.enums import CustomerId, EventType, LoadState, SOPBranch
from src.domain.exceptions import InvalidEventError, LoadNotFoundError
from src.domain.models import Event, Load, AgentRun


def make_load(**overrides):
    """Helper to create a Load with all required fields."""
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
    """Helper to create an Event with all required fields."""
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


@pytest.fixture
def mock_load_repo():
    return AsyncMock()


@pytest.fixture
def mock_event_repo():
    return AsyncMock()


@pytest.fixture
def mock_event_queue():
    return AsyncMock()


@pytest.fixture
def mock_agent_run_repo():
    return AsyncMock()


@pytest.fixture
def mock_orchestrator():
    orchestrator = AsyncMock()
    orchestrator.run = AsyncMock(return_value={
        "run_id": "run-1",
        "tool_calls": [{"tool": "send_sms", "arguments": {}, "result": {}}],
        "memory_operations": [{"operation": "add", "content": "test"}],
    })
    return orchestrator


@pytest.fixture
def sample_load():
    return make_load()


@pytest.fixture
def sample_event():
    return make_event()


class TestEventProcessorInit:
    def test_init_with_all_deps(self, mock_load_repo, mock_event_repo, mock_event_queue, mock_agent_run_repo, mock_orchestrator):
        processor = EventProcessor(
            load_repo=mock_load_repo, event_repo=mock_event_repo,
            event_queue=mock_event_queue, agent_run_repo=mock_agent_run_repo,
            orchestrator=mock_orchestrator,
        )
        assert processor._load_repo is mock_load_repo
        assert processor._event_queue is mock_event_queue
        assert processor._orchestrator is mock_orchestrator

    def test_init_with_minimal_deps(self, mock_load_repo, mock_event_repo):
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        assert processor._event_queue is None
        assert processor._agent_run_repo is None
        assert processor._orchestrator is None


class TestEventProcessorProcess:
    @pytest.mark.asyncio
    async def test_process_with_orchestrator(self, mock_load_repo, mock_event_repo, mock_event_queue, mock_agent_run_repo, mock_orchestrator, sample_load, sample_event):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_event_repo.mark_processed = AsyncMock()
        mock_event_queue.enqueue = AsyncMock()

        processor = EventProcessor(
            load_repo=mock_load_repo, event_repo=mock_event_repo,
            event_queue=mock_event_queue, agent_run_repo=mock_agent_run_repo,
            orchestrator=mock_orchestrator,
        )
        result = await processor.process("evt-1", "load-1")
        assert result["event_id"] == "evt-1"
        assert result["status"] == "completed"
        assert result["workflow"] == "delivery_eta_checkpoint"
        mock_event_repo.mark_processed.assert_called_once_with("evt-1")
        mock_orchestrator.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_without_orchestrator(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, sample_load, sample_event):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_event_repo.mark_processed = AsyncMock()
        mock_agent_run_repo.save = AsyncMock()

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo, agent_run_repo=mock_agent_run_repo)
        result = await processor.process("evt-1", "load-1")
        assert result["status"] == "routed"
        mock_agent_run_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_without_orchestrator_or_agent_run_repo(self, mock_load_repo, mock_event_repo, sample_load, sample_event):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_event_repo.mark_processed = AsyncMock()

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        result = await processor.process("evt-1", "load-1")
        assert result["status"] == "routed"

    @pytest.mark.asyncio
    async def test_process_orchestrator_failure_fallback(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, sample_load, sample_event):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_event_repo.mark_processed = AsyncMock()
        mock_agent_run_repo.save = AsyncMock()

        failing_orchestrator = AsyncMock()
        failing_orchestrator.run = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo, agent_run_repo=mock_agent_run_repo, orchestrator=failing_orchestrator)
        result = await processor.process("evt-1", "load-1")
        assert result["status"] == "routed"
        mock_agent_run_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_routes_to_confirm_delivery(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, mock_orchestrator):
        load_at_delivery = make_load(load_id="load-2", current_state=LoadState.AT_DELIVERY)
        event = make_event(event_id="evt-2", load_id="load-2")
        mock_event_repo.get_by_id = AsyncMock(return_value=event)
        mock_load_repo.get_by_id = AsyncMock(return_value=load_at_delivery)
        mock_event_repo.mark_processed = AsyncMock()

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo, agent_run_repo=mock_agent_run_repo, orchestrator=mock_orchestrator)
        result = await processor.process("evt-2", "load-2")
        assert result["workflow"] == "confirm_delivery"

    @pytest.mark.asyncio
    async def test_process_without_event_queue(self, mock_load_repo, mock_event_repo, mock_agent_run_repo, mock_orchestrator, sample_load, sample_event):
        mock_event_repo.get_by_id = AsyncMock(return_value=sample_event)
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_event_repo.mark_processed = AsyncMock()

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo, event_queue=None, agent_run_repo=mock_agent_run_repo, orchestrator=mock_orchestrator)
        result = await processor.process("evt-1", "load-1")
        assert result["status"] == "completed"


class TestEventProcessorValidateEvent:
    @pytest.mark.asyncio
    async def test_validate_event_wrong_load(self, mock_load_repo, mock_event_repo):
        event_wrong_load = make_event(load_id="load-OTHER")
        load = make_load()
        mock_event_repo.get_by_id = AsyncMock(return_value=event_wrong_load)
        mock_load_repo.get_by_id = AsyncMock(return_value=load)

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        with pytest.raises(InvalidEventError):
            await processor.process("evt-1", "load-1")

    @pytest.mark.asyncio
    async def test_validate_event_inactive_state(self, mock_load_repo, mock_event_repo):
        delivered_load = make_load(current_state=LoadState.DELIVERED)
        event = make_event()
        mock_event_repo.get_by_id = AsyncMock(return_value=event)
        mock_load_repo.get_by_id = AsyncMock(return_value=delivered_load)

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        with pytest.raises(InvalidEventError):
            await processor.process("evt-1", "load-1")


class TestEventProcessorDetermineWorkflow:
    def test_determine_workflow_dispatched(self, mock_load_repo, mock_event_repo):
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.DISPATCHED)
        event = make_event(event_type=EventType.TRACKING)
        assert processor._determine_workflow(event, load) == "delivery_eta_checkpoint"

    def test_determine_workflow_on_route(self, mock_load_repo, mock_event_repo):
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.ON_ROUTE_TO_DELIVERY)
        event = make_event(event_type=EventType.TRACKING)
        assert processor._determine_workflow(event, load) == "delivery_eta_checkpoint"

    def test_determine_workflow_at_delivery(self, mock_load_repo, mock_event_repo):
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.AT_DELIVERY)
        event = make_event(event_type=EventType.TRACKING)
        assert processor._determine_workflow(event, load) == "confirm_delivery"

    def test_determine_workflow_confirm_delivery(self, mock_load_repo, mock_event_repo):
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.CONFIRM_DELIVERY)
        event = make_event(event_type=EventType.INBOUND_COMMUNICATION)
        assert processor._determine_workflow(event, load) == "confirm_delivery"

    def test_determine_workflow_default(self, mock_load_repo, mock_event_repo):
        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        load = make_load(current_state=LoadState.DISPATCHED)
        event = make_event(event_type=EventType.LOAD_UPDATE)
        result = processor._determine_workflow(event, load)
        assert result in ("delivery_eta_checkpoint", "confirm_delivery")


class TestEventProcessorTimerCallback:
    @pytest.mark.asyncio
    async def test_process_timer_callback(self, mock_load_repo, mock_event_repo, sample_load):
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_event_repo.save = AsyncMock()

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        result = await processor.process_timer_callback("timer-1", "load-1")
        assert result["load_id"] == "load-1"
        assert result["status"] == "timer_routed"
        mock_event_repo.save.assert_called_once()