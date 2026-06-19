"""Extended tests for API route handlers using FastAPI TestClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.domain.enums import CustomerId, EventType, LoadState
from src.domain.models import Load, Event, AgentRun, ToolCall


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


def make_agent_run(**overrides):
    defaults = dict(
        run_id="run-1",
        event_id="evt-1",
        load_id="load-1",
        customer_id=CustomerId.CUSTOMER_A,
        workflow="delivery_eta_checkpoint",
        sop_branch="eta_followup",
        customer_rules_applied=[],
        tool_calls=[],
        memory_operations=[],
        state_before=LoadState.DISPATCHED,
        state_after=LoadState.ON_ROUTE_TO_DELIVERY,
        status="completed",
        error=None,
        trace_id=None,
        started_at=datetime.now(timezone.utc).isoformat(),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(overrides)
    return AgentRun(**defaults)


# --- Test App Creation and Configuration ---

class TestAppCreation:
    """Tests for app creation and configuration."""

    def test_create_app_returns_fastapi_app(self):
        from src.interfaces.app import create_app
        from fastapi import FastAPI
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_app_has_health_endpoint(self):
        from src.interfaces.app import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_app_has_loads_router(self):
        from src.interfaces.app import app
        routes = [r.path for r in app.routes]
        assert any("/api/v1/loads" in r for r in routes)

    def test_app_has_events_router(self):
        from src.interfaces.app import app
        routes = [r.path for r in app.routes]
        assert any("/api/v1/events" in r for r in routes)

    def test_app_has_monitoring_router(self):
        from src.interfaces.app import app
        routes = [r.path for r in app.routes]
        assert any("/api/v1/monitoring" in r for r in routes)

    def test_app_has_debugger_router(self):
        from src.interfaces.app import app
        routes = [r.path for r in app.routes]
        assert any("/api/v1/debugger" in r for r in routes)

    def test_app_version_in_health(self):
        from src.interfaces.app import app
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "version" in data


# --- Test Loads Routes ---

class TestLoadsRoutes:
    """Tests for loads route endpoints."""

    @pytest.mark.asyncio
    async def test_get_load_service_raises_when_no_db(self):
        """Test that get_load_service raises 503 when no database."""
        from src.interfaces.routes.loads import get_load_service
        with pytest.raises(Exception):
            # When session is None, it should raise HTTPException
            import asyncio
            try:
                await get_load_service(None)
            except Exception as e:
                # Should be HTTPException with 503
                assert "503" in str(e) or "Database" in str(e) or "Service" in str(e)
                raise

    def test_loads_router_has_create_endpoint(self):
        from src.interfaces.routes.loads import router
        routes = [r.path for r in router.routes]
        assert "/" in routes

    def test_loads_router_has_get_endpoint(self):
        from src.interfaces.routes.loads import router
        routes = [r.path for r in router.routes]
        assert "/{load_id}" in routes

    def test_loads_router_has_active_loads_endpoint(self):
        from src.interfaces.routes.loads import router
        routes = [r.path for r in router.routes]
        assert "/" in routes

    def test_loads_router_has_transition_endpoint(self):
        from src.interfaces.routes.loads import router
        routes = [r.path for r in router.routes]
        assert "/{load_id}/transition" in routes


# --- Test Events Routes ---

class TestEventsRoutes:
    """Tests for events route endpoints."""

    def test_events_router_has_inbound_communication(self):
        from src.interfaces.routes.events import router
        routes = [r.path for r in router.routes]
        assert "/inbound-communication" in routes

    def test_events_router_has_tracking(self):
        from src.interfaces.routes.events import router
        routes = [r.path for r in router.routes]
        assert "/tracking" in routes

    def test_events_router_has_load_update(self):
        from src.interfaces.routes.events import router
        routes = [r.path for r in router.routes]
        assert "/load-update" in routes

    def test_events_router_has_submit_task(self):
        from src.interfaces.routes.events import router
        routes = [r.path for r in router.routes]
        assert "/submit-task" in routes

    def test_create_orchestrator_creates_instance(self):
        """Test _create_orchestrator creates an AgentOrchestrator."""
        from src.interfaces.routes.events import _create_orchestrator
        from src.agent.orchestrator import AgentOrchestrator
        mock_session = MagicMock()
        with patch("src.interfaces.routes.events.get_load_repository", return_value=AsyncMock()), \
             patch("src.interfaces.routes.events.get_event_repository", return_value=AsyncMock()), \
             patch("src.interfaces.routes.events.get_agent_run_repository", return_value=AsyncMock()), \
             patch("src.interfaces.routes.events.get_llm", return_value=MagicMock()):
            orchestrator = _create_orchestrator(mock_session)
            assert isinstance(orchestrator, AgentOrchestrator)


# --- Test Monitoring Routes ---

class TestMonitoringRoutes:
    """Tests for monitoring route endpoints."""

    def test_monitoring_router_has_dashboard(self):
        from src.interfaces.routes.monitoring import router
        routes = [r.path for r in router.routes]
        assert "/dashboard" in routes

    def test_monitoring_router_has_agent_runs(self):
        from src.interfaces.routes.monitoring import router
        routes = [r.path for r in router.routes]
        assert "/agent-runs" in routes

    def test_monitoring_router_has_memory_metrics(self):
        from src.interfaces.routes.monitoring import router
        routes = [r.path for r in router.routes]
        assert "/memory-metrics" in routes

    def test_monitoring_router_has_failures(self):
        from src.interfaces.routes.monitoring import router
        routes = [r.path for r in router.routes]
        assert "/failures" in routes

    def test_monitoring_router_has_scheduled_followups(self):
        from src.interfaces.routes.monitoring import router
        routes = [r.path for r in router.routes]
        assert "/scheduled-followups" in routes


# --- Test Debugger Routes ---

class TestDebuggerRoutes:
    """Tests for debugger route endpoints."""

    def test_debugger_router_has_agent_runs(self):
        from src.interfaces.routes.debugger import router
        routes = [r.path for r in router.routes]
        assert "/agent-runs/{run_id}" in routes

    def test_debugger_router_has_load_history(self):
        from src.interfaces.routes.debugger import router
        routes = [r.path for r in router.routes]
        assert "/loads/{load_id}/history" in routes

    def test_debugger_router_has_memory_state(self):
        from src.interfaces.routes.debugger import router
        routes = [r.path for r in router.routes]
        assert "/memory/{scope}/{scope_id}" in routes

    def test_debugger_router_has_add_memory(self):
        from src.interfaces.routes.debugger import router
        routes = [r.path for r in router.routes]
        assert "/memory/add" in routes

    def test_debugger_router_has_delete_memory(self):
        from src.interfaces.routes.debugger import router
        routes = [r.path for r in router.routes]
        assert "/memory/{memory_id}" in routes

    def test_debugger_router_has_workflows(self):
        from src.interfaces.routes.debugger import router
        routes = [r.path for r in router.routes]
        assert "/workflows" in routes

    def test_debugger_router_has_workflow_test(self):
        from src.interfaces.routes.debugger import router
        routes = [r.path for r in router.routes]
        assert "/workflows/{workflow}/test" in routes


# --- Test EventProcessor Integration ---

class TestEventProcessorIntegration:
    """Integration tests for event processing logic."""

    @pytest.mark.asyncio
    async def test_process_event_with_tracking(self):
        """Test processing a tracking event."""
        from src.application.services.event_processor import EventProcessor
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()

        load = make_load(current_state=LoadState.ON_ROUTE_TO_DELIVERY)
        event = make_event(event_type=EventType.TRACKING, event_data={"eta": "2 hours"})

        mock_event_repo.get_by_id = AsyncMock(return_value=event)
        mock_load_repo.get_by_id = AsyncMock(return_value=load)
        mock_event_repo.mark_processed = AsyncMock()

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        result = await processor.process("evt-1", "load-1")
        assert result["workflow"] == "delivery_eta_checkpoint"

    @pytest.mark.asyncio
    async def test_process_event_with_load_update(self):
        """Test processing a load update event."""
        from src.application.services.event_processor import EventProcessor
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()

        load = make_load(current_state=LoadState.DISPATCHED)
        event = make_event(event_type=EventType.LOAD_UPDATE, event_data={"update": "route changed"})

        mock_event_repo.get_by_id = AsyncMock(return_value=event)
        mock_load_repo.get_by_id = AsyncMock(return_value=load)
        mock_event_repo.mark_processed = AsyncMock()

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        result = await processor.process("evt-1", "load-1")
        assert result["workflow"] == "delivery_eta_checkpoint"

    @pytest.mark.asyncio
    async def test_process_event_at_delivery(self):
        """Test processing an event when load is at delivery."""
        from src.application.services.event_processor import EventProcessor
        mock_load_repo = AsyncMock()
        mock_event_repo = AsyncMock()

        load = make_load(current_state=LoadState.AT_DELIVERY)
        event = make_event(event_type=EventType.INBOUND_COMMUNICATION, event_data={"message": "arrived"})

        mock_event_repo.get_by_id = AsyncMock(return_value=event)
        mock_load_repo.get_by_id = AsyncMock(return_value=load)
        mock_event_repo.mark_processed = AsyncMock()

        processor = EventProcessor(load_repo=mock_load_repo, event_repo=mock_event_repo)
        result = await processor.process("evt-1", "load-1")
        assert result["workflow"] == "confirm_delivery"


# --- Test LoadService Methods ---

class TestLoadServiceMethods:
    """Tests for LoadService methods."""

    @pytest.mark.asyncio
    async def test_load_to_dict_with_eta(self):
        """Test _load_to_dict includes ETA."""
        from src.application.services.load_service import LoadService
        load = make_load(current_eta_utc="2024-06-01T12:00:00Z")
        mock_repo = AsyncMock()
        service = LoadService(load_repo=mock_repo)
        result = service._load_to_dict(load)
        assert result["current_eta_utc"] == "2024-06-01T12:00:00Z"

    @pytest.mark.asyncio
    async def test_load_to_dict_with_load_data(self):
        """Test _load_to_dict includes load_data."""
        from src.application.services.load_service import LoadService
        load = make_load(load_data={"origin": "Chicago", "destination": "Dallas"})
        mock_repo = AsyncMock()
        service = LoadService(load_repo=mock_repo)
        result = service._load_to_dict(load)
        assert result["load_data"]["origin"] == "Chicago"

    @pytest.mark.asyncio
    async def test_get_active_loads(self):
        """Test get_active_loads returns list of ActiveLoadSummary."""
        from src.application.services.load_service import LoadService
        from src.application.dto import ActiveLoadSummary
        load1 = make_load(load_id="load-1")
        load2 = make_load(load_id="load-2", current_state=LoadState.ON_ROUTE_TO_DELIVERY)
        mock_repo = AsyncMock()
        mock_repo.get_active_loads = AsyncMock(return_value=[load1, load2])
        service = LoadService(load_repo=mock_repo)
        result = await service.get_active_loads()
        assert len(result) == 2
        assert isinstance(result[0], ActiveLoadSummary)
        assert result[0].load_id == "load-1"

    @pytest.mark.asyncio
    async def test_get_load_not_found(self):
        """Test get_load raises when load not found."""
        from src.application.services.load_service import LoadService
        from src.domain.exceptions import LoadNotFoundError
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(side_effect=LoadNotFoundError("load-999"))
        service = LoadService(load_repo=mock_repo)
        with pytest.raises(LoadNotFoundError):
            await service.get_load("load-999")

    @pytest.mark.asyncio
    async def test_create_load(self):
        """Test create_load creates and returns a load."""
        from src.application.services.load_service import LoadService
        from src.application.dto import CreateLoadRequest
        mock_repo = AsyncMock()
        load = make_load()
        mock_repo.save = AsyncMock(return_value=load)
        service = LoadService(load_repo=mock_repo)
        request = CreateLoadRequest(
            customer_id=CustomerId.CUSTOMER_A,
            external_load_id="ext-1",
        )
        result = await service.create_load(request)
        assert result is not None

    @pytest.mark.asyncio
    async def test_transition_state_success(self):
        """Test successful state transition."""
        from src.application.services.load_service import LoadService
        from src.application.dto import StateTransitionSummary
        load = make_load(current_state=LoadState.DISPATCHED)
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=load)
        mock_repo.save = AsyncMock(return_value=load)
        service = LoadService(load_repo=mock_repo)
        result = await service.transition_state("load-1", LoadState.ON_ROUTE_TO_DELIVERY)
        assert result.from_state == LoadState.DISPATCHED
        assert result.to_state == LoadState.ON_ROUTE_TO_DELIVERY


# --- Test RedisEventQueue ---

class TestRedisEventQueue:
    """Tests for RedisEventQueue - testing what we can without instantiating the ABC."""

    def test_redis_event_queue_has_enqueue_method(self):
        """Test that RedisEventQueue has enqueue method."""
        from src.infrastructure.repositories import RedisEventQueue
        assert hasattr(RedisEventQueue, 'enqueue')

    def test_redis_event_queue_has_dequeue_method(self):
        """Test that RedisEventQueue has dequeue method."""
        from src.infrastructure.repositories import RedisEventQueue
        assert hasattr(RedisEventQueue, 'dequeue')

    def test_redis_event_queue_has_size_method(self):
        """Test that RedisEventQueue has size method."""
        from src.infrastructure.repositories import RedisEventQueue
        assert hasattr(RedisEventQueue, 'size')

    def test_redis_event_queue_inherits_from_event_queue(self):
        """Test that RedisEventQueue inherits from EventQueue."""
        from src.infrastructure.repositories import RedisEventQueue, EventQueue
        assert issubclass(RedisEventQueue, EventQueue)

    def test_event_queue_is_abstract(self):
        """Test that EventQueue is an abstract class."""
        from src.infrastructure.repositories import EventQueue
        from abc import ABC
        assert issubclass(EventQueue, ABC)

    def test_event_queue_abstract_methods(self):
        """Test that EventQueue defines expected abstract methods."""
        from src.infrastructure.repositories import EventQueue
        abstract_methods = EventQueue.__abstractmethods__
        assert 'enqueue' in abstract_methods
        assert 'enqueue_timer_callback' in abstract_methods
        assert 'cancel_timer' in abstract_methods
        assert 'cancel_timers_by_type' in abstract_methods


# --- Test SqlAlchemyAgentRunRepository ---

class TestSqlAlchemyAgentRunRepository:
    """Tests for SqlAlchemyAgentRunRepository conversion methods."""

    def test_to_domain(self):
        from src.infrastructure.repositories import SqlAlchemyAgentRunRepository
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)
        mock_model = MagicMock()
        mock_model.run_id = MagicMock()
        mock_model.run_id.__str__ = lambda self: "12345678-1234-1234-1234-123456789012"
        mock_model.event_id = "evt-1"
        mock_model.load_id = "load-1"
        mock_model.customer_id = "customer_a"
        mock_model.workflow = "delivery_eta_checkpoint"
        mock_model.sop_branch = "eta_followup"
        mock_model.customer_rules_applied = []
        mock_model.tool_calls = []
        mock_model.memory_operations = []
        mock_model.state_before = "dispatched"
        mock_model.state_after = "on_route_to_delivery"
        mock_model.status = "completed"
        mock_model.error = None
        mock_model.trace_id = None
        mock_model.started_at = datetime.now(timezone.utc)
        mock_model.completed_at = None

        result = repo._to_domain(mock_model)
        assert result.workflow == "delivery_eta_checkpoint"
        assert result.status == "completed"
        assert result.load_id == "load-1"

    def test_to_domain_with_none_states(self):
        from src.infrastructure.repositories import SqlAlchemyAgentRunRepository
        from src.domain.enums import LoadState
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)
        mock_model = MagicMock()
        mock_model.run_id = MagicMock()
        mock_model.run_id.__str__ = lambda self: "12345678-1234-1234-1234-123456789012"
        mock_model.event_id = "evt-1"
        mock_model.load_id = "load-1"
        mock_model.customer_id = "customer_a"
        mock_model.workflow = "confirm_delivery"
        mock_model.sop_branch = None
        mock_model.customer_rules_applied = None
        mock_model.tool_calls = None
        mock_model.memory_operations = None
        mock_model.state_before = "dispatched"
        mock_model.state_after = None
        mock_model.status = "running"
        mock_model.error = None
        mock_model.trace_id = None
        mock_model.started_at = datetime.now(timezone.utc)
        mock_model.completed_at = None

        result = repo._to_domain(mock_model)
        assert result.state_before == LoadState.DISPATCHED
        assert result.state_after is None
        assert result.tool_calls == []
        assert result.memory_operations == []


# --- Test SqlAlchemyMemoryRepository Additional Methods ---

class TestSqlAlchemyMemoryRepositoryAdditional:
    """Additional tests for SqlAlchemyMemoryRepository."""

    def test_model_to_dict_with_enum_types(self):
        """Test _model_to_dict with enum memory_type and scope."""
        from src.infrastructure.repositories import SqlAlchemyMemoryRepository
        from src.domain.enums import MemoryType, MemoryScope
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)
        mock_model = MagicMock()
        mock_model.id = MagicMock()
        mock_model.memory_type = MemoryType.EPISODIC
        mock_model.scope = MemoryScope.LOAD
        mock_model.scope_id = "load-1"
        mock_model.content = "test content"
        mock_model.summary = "summary"
        mock_model.tags = ["test"]
        mock_model.source_event_ids = ["evt-1"]
        mock_model.confidence = 0.95
        mock_model.relevance_score = 0.85
        mock_model.access_count = 10
        mock_model.content_type = "fact"
        mock_model.created_at = MagicMock()
        mock_model.created_at.isoformat.return_value = "2024-01-01T00:00:00Z"
        mock_model.updated_at = MagicMock()
        mock_model.updated_at.isoformat.return_value = "2024-01-02T00:00:00Z"
        mock_model.expires_at = None

        result = repo._model_to_dict(mock_model)
        assert result["memory_type"] == "episodic"
        assert result["scope"] == "load"
        assert result["confidence"] == 0.95
        assert result["relevance_score"] == 0.85
        assert result["access_count"] == 10

    def test_model_to_dict_with_expires_at(self):
        """Test _model_to_dict with expires_at set."""
        from src.infrastructure.repositories import SqlAlchemyMemoryRepository
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)
        mock_model = MagicMock()
        mock_model.id = MagicMock()
        mock_model.memory_type = "episodic"
        mock_model.scope = "load"
        mock_model.scope_id = "load-1"
        mock_model.content = "test content"
        mock_model.summary = None
        mock_model.tags = []
        mock_model.source_event_ids = []
        mock_model.confidence = 0.9
        mock_model.relevance_score = 0.8
        mock_model.access_count = 5
        mock_model.content_type = "fact"
        mock_model.created_at = MagicMock()
        mock_model.created_at.isoformat.return_value = "2024-01-01T00:00:00Z"
        mock_model.updated_at = None
        mock_model.expires_at = MagicMock()
        mock_model.expires_at.isoformat.return_value = "2024-12-31T23:59:59Z"

        result = repo._model_to_dict(mock_model)
        assert result["expires_at"] == "2024-12-31T23:59:59Z"


# --- Test Celery Tasks ---

class TestCeleryTasks:
    """Tests for Celery task definitions."""

    def test_process_event_task_exists(self):
        """Test that process_event task is registered."""
        from src.infrastructure.queue import process_event
        assert process_event is not None
        assert callable(process_event)

    def test_run_agent_workflow_task_exists(self):
        """Test that run_agent_workflow task is registered."""
        from src.infrastructure.queue import run_agent_workflow
        assert run_agent_workflow is not None
        assert callable(run_agent_workflow)

    def test_fire_timer_task_exists(self):
        """Test that fire_timer task is registered."""
        from src.infrastructure.queue import fire_timer
        assert fire_timer is not None
        assert callable(fire_timer)

    def test_memory_maintenance_task_exists(self):
        """Test that memory_maintenance task is registered."""
        from src.infrastructure.queue import memory_maintenance
        assert memory_maintenance is not None
        assert callable(memory_maintenance)

    def test_process_event_task_name(self):
        """Test that process_event task has correct name."""
        from src.infrastructure.queue import process_event
        assert process_event.name == "src.infrastructure.queue.process_event"

    def test_run_agent_workflow_task_name(self):
        """Test that run_agent_workflow task has correct name."""
        from src.infrastructure.queue import run_agent_workflow
        assert run_agent_workflow.name == "src.infrastructure.queue.run_agent_workflow"

    def test_fire_timer_task_name(self):
        """Test that fire_timer task has correct name."""
        from src.infrastructure.queue import fire_timer
        assert fire_timer.name == "src.infrastructure.queue.fire_timer"

    def test_memory_maintenance_task_name(self):
        """Test that memory_maintenance task has correct name."""
        from src.infrastructure.queue import memory_maintenance
        assert memory_maintenance.name == "src.infrastructure.queue.memory_maintenance"