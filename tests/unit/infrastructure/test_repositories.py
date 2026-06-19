"""Tests for infrastructure repositories - unit tests for factory functions, conversion methods, and queue tasks."""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.enums import CustomerId, EventType, LoadState, MemoryOperation, MemoryScope, MemoryType
from src.domain.models import Event, Load, ToolCall, MemoryOperationLog
from src.infrastructure.repositories import (
    SqlAlchemyLoadRepository,
    SqlAlchemyEventRepository,
    SqlAlchemyToolCallRepository,
    SqlAlchemyAgentRunRepository,
    SqlAlchemyMemoryRepository,
    SqlAlchemyMemoryOperationLogRepository,
    get_load_repository,
    get_event_repository,
    get_tool_call_repository,
    get_agent_run_repository,
    get_memory_repository,
    get_memory_operation_log_repository,
)


# --- Factory Function Tests ---

class TestRepositoryFactories:
    """Tests for repository factory functions."""

    def test_get_load_repository(self):
        mock_session = AsyncMock()
        repo = get_load_repository(mock_session)
        assert isinstance(repo, SqlAlchemyLoadRepository)

    def test_get_event_repository(self):
        mock_session = AsyncMock()
        repo = get_event_repository(mock_session)
        assert isinstance(repo, SqlAlchemyEventRepository)

    def test_get_tool_call_repository(self):
        mock_session = AsyncMock()
        repo = get_tool_call_repository(mock_session)
        assert isinstance(repo, SqlAlchemyToolCallRepository)

    def test_get_agent_run_repository(self):
        mock_session = AsyncMock()
        repo = get_agent_run_repository(mock_session)
        assert isinstance(repo, SqlAlchemyAgentRunRepository)

    def test_get_memory_repository(self):
        mock_session = AsyncMock()
        repo = get_memory_repository(mock_session)
        assert isinstance(repo, SqlAlchemyMemoryRepository)

    def test_get_memory_operation_log_repository(self):
        mock_session = AsyncMock()
        repo = get_memory_operation_log_repository(mock_session)
        assert isinstance(repo, SqlAlchemyMemoryOperationLogRepository)


# --- SqlAlchemyLoadRepository Unit Tests ---

class TestSqlAlchemyLoadRepository:
    """Tests for SqlAlchemyLoadRepository - conversion methods."""

    def test_to_model(self):
        """Test _to_model converts Load domain model to SQLAlchemy model."""
        mock_session = AsyncMock()
        repo = SqlAlchemyLoadRepository(mock_session)
        load = Load(
            load_id="load-1",
            customer_id=CustomerId.CUSTOMER_A,
            external_load_id="ext-1",
            current_state=LoadState.DISPATCHED,
            load_data={"origin": "A"},
        )
        model = repo._to_model(load)
        assert model.load_id == "load-1"
        assert model.customer_id == CustomerId.CUSTOMER_A
        assert model.current_state == LoadState.DISPATCHED

    def test_to_domain(self):
        """Test _to_domain converts SQLAlchemy model to Load domain model."""
        mock_session = AsyncMock()
        repo = SqlAlchemyLoadRepository(mock_session)
        mock_model = MagicMock()
        mock_model.load_id = "load-1"
        mock_model.customer_id = "customer_a"
        mock_model.external_load_id = "ext-1"
        mock_model.po_number = "PO-123"
        mock_model.instructions = None
        mock_model.load_data = {}
        mock_model.current_state = "dispatched"
        mock_model.current_eta_utc = None
        mock_model.created_at = datetime.now(timezone.utc)
        mock_model.updated_at = datetime.now(timezone.utc)

        load = repo._to_domain(mock_model)
        assert load.load_id == "load-1"
        assert load.customer_id == CustomerId.CUSTOMER_A
        assert load.current_state == LoadState.DISPATCHED


# --- SqlAlchemyEventRepository Unit Tests ---

class TestSqlAlchemyEventRepository:
    """Tests for SqlAlchemyEventRepository - conversion methods."""

    def test_to_domain(self):
        mock_session = AsyncMock()
        repo = SqlAlchemyEventRepository(mock_session)
        mock_model = MagicMock()
        mock_model.event_id = "evt-1"
        mock_model.event_type = "inbound_communication"
        mock_model.load_id = "load-1"
        mock_model.customer_id = "customer_a"
        mock_model.occurred_at = "2024-01-01T00:00:00Z"
        mock_model.event_data = {}

        event = repo._to_domain(mock_model)
        assert event.event_id == "evt-1"
        assert event.event_type == EventType.INBOUND_COMMUNICATION

    def test_to_model(self):
        mock_session = AsyncMock()
        repo = SqlAlchemyEventRepository(mock_session)
        event = Event(
            event_id="evt-1",
            event_type=EventType.INBOUND_COMMUNICATION,
            load_id="load-1",
            customer_id=CustomerId.CUSTOMER_A,
            occurred_at="2024-01-01T00:00:00Z",
            event_data={},
        )

        model = repo._to_model(event)
        assert model.event_id == "evt-1"
        assert model.event_type == EventType.INBOUND_COMMUNICATION


# --- SqlAlchemyToolCallRepository Unit Tests ---

class TestSqlAlchemyToolCallRepository:
    """Tests for SqlAlchemyToolCallRepository - conversion methods."""

    def test_to_domain(self):
        mock_session = AsyncMock()
        repo = SqlAlchemyToolCallRepository(mock_session)
        mock_model = MagicMock()
        mock_model.tool_call_id = "tc-1"
        mock_model.event_id = "evt-1"
        mock_model.load_id = "load-1"
        mock_model.tool = "send_sms"
        mock_model.arguments = {"to": "+1234567890"}
        mock_model.result = {"status": "sent"}

        tc = repo._to_domain(mock_model)
        assert tc.tool == "send_sms"
        assert tc.event_id == "evt-1"


# --- SqlAlchemyMemoryRepository Unit Tests ---

class TestSqlAlchemyMemoryRepository:
    """Tests for SqlAlchemyMemoryRepository - model_to_dict."""

    def test_model_to_dict(self):
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)
        mock_model = MagicMock()
        mock_model.id = MagicMock()
        mock_model.memory_type = "episodic"
        mock_model.scope = "load"
        mock_model.scope_id = "load-1"
        mock_model.content = "test content"
        mock_model.summary = None
        mock_model.tags = ["test"]
        mock_model.source_event_ids = []
        mock_model.confidence = 0.9
        mock_model.relevance_score = 0.8
        mock_model.access_count = 5
        mock_model.content_type = "fact"
        mock_model.created_at = MagicMock()
        mock_model.created_at.isoformat.return_value = "2024-01-01T00:00:00Z"
        mock_model.updated_at = None
        mock_model.expires_at = None

        result = repo._model_to_dict(mock_model)
        assert result["content"] == "test content"
        assert result["scope_id"] == "load-1"
        assert result["confidence"] == 0.9
        assert result["tags"] == ["test"]


# --- SqlAlchemyMemoryOperationLogRepository Unit Tests ---

class TestSqlAlchemyMemoryOperationLogRepository:
    """Tests for SqlAlchemyMemoryOperationLogRepository - conversion methods."""

    def test_to_domain(self):
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryOperationLogRepository(mock_session)
        mock_model = MagicMock()
        mock_model.operation_id = "op-1"
        mock_model.event_id = "evt-1"
        mock_model.load_id = "load-1"
        mock_model.operation = "add"
        mock_model.memory_type = "episodic"
        mock_model.scope = "load"
        mock_model.scope_id = "load-1"
        mock_model.content = "test content"
        mock_model.result = {}

        log = repo._to_domain(mock_model)
        assert log.operation_id == "op-1"
        assert log.event_id == "evt-1"


# --- Celery Queue Task Tests ---

class TestCeleryQueueConfiguration:
    """Tests for Celery queue configuration."""

    def test_celery_app_exists(self):
        """Test that celery_app is properly configured."""
        from src.infrastructure.queue import celery_app
        assert celery_app is not None
        assert celery_app.conf["task_serializer"] == "json"
        assert celery_app.conf["result_serializer"] == "json"
        assert celery_app.conf["timezone"] == "UTC"

    def test_celery_task_routes(self):
        """Test that task routes are configured."""
        from src.infrastructure.queue import celery_app
        routes = celery_app.conf["task_routes"]
        assert "src.infrastructure.queue.tasks.process_event" in routes
        assert routes["src.infrastructure.queue.tasks.process_event"]["queue"] == "events"
        assert "src.infrastructure.queue.tasks.run_agent_workflow" in routes
        assert routes["src.infrastructure.queue.tasks.run_agent_workflow"]["queue"] == "agent"
        assert "src.infrastructure.queue.tasks.fire_timer" in routes
        assert routes["src.infrastructure.queue.tasks.fire_timer"]["queue"] == "timers"
        assert "src.infrastructure.queue.tasks.memory_maintenance" in routes
        assert routes["src.infrastructure.queue.tasks.memory_maintenance"]["queue"] == "memory"

    def test_celery_app_settings(self):
        """Test celery app configuration values."""
        from src.infrastructure.queue import celery_app
        assert celery_app.conf["enable_utc"] is True
        assert celery_app.conf["task_track_started"] is True
        assert celery_app.conf["task_acks_late"] is True