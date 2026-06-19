"""Tests for infrastructure repositories - async method tests using mocks."""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import (
    CustomerId, EventType, LoadState, MemoryScope, MemoryType, MemoryOperation,
)
from src.domain.models import Load, Event, ToolCall, AgentRun, MemoryOperationLog
from src.domain.exceptions import LoadNotFoundError
from src.infrastructure.repositories import (
    SqlAlchemyLoadRepository,
    SqlAlchemyEventRepository,
    SqlAlchemyToolCallRepository,
    SqlAlchemyAgentRunRepository,
    SqlAlchemyMemoryRepository,
    SqlAlchemyMemoryOperationLogRepository,
)


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
        event_data={"message": "test"},
    )
    defaults.update(overrides)
    return Event(**defaults)


def make_tool_call(**overrides):
    defaults = dict(
        tool_call_id="tc-1",
        event_id="evt-1",
        load_id="load-1",
        tool="send_sms",
        arguments={"to": "+1234567890"},
        result={"status": "sent"},
    )
    defaults.update(overrides)
    return ToolCall(**defaults)


def make_agent_run(**overrides):
    defaults = dict(
        run_id=str(uuid.uuid4()),
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


# --- SqlAlchemyLoadRepository Async Method Tests ---

class TestSqlAlchemyLoadRepositoryAsync:
    """Tests for SqlAlchemyLoadRepository async methods."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Test get_by_id returns load when found."""
        mock_session = AsyncMock()
        repo = SqlAlchemyLoadRepository(mock_session)

        mock_result = MagicMock()
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
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute = AsyncMock(return_value=mock_result)

        load = await repo.get_by_id("load-1")
        assert load.load_id == "load-1"
        assert load.customer_id == CustomerId.CUSTOMER_A

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test get_by_id raises LoadNotFoundError when not found."""
        mock_session = AsyncMock()
        repo = SqlAlchemyLoadRepository(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(LoadNotFoundError):
            await repo.get_by_id("load-nonexistent")

    @pytest.mark.asyncio
    async def test_get_active_loads(self):
        """Test get_active_loads returns list of loads."""
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

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        loads = await repo.get_active_loads()
        assert len(loads) == 1
        assert loads[0].load_id == "load-1"

    @pytest.mark.asyncio
    async def test_save_new_load(self):
        """Test save adds new load."""
        mock_session = AsyncMock()
        repo = SqlAlchemyLoadRepository(mock_session)

        load = make_load()

        # Mock existing check - no existing load
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_existing_result)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        result = await repo.save(load)
        assert result.load_id == "load-1"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_existing_load(self):
        """Test save merges existing load."""
        mock_session = AsyncMock()
        repo = SqlAlchemyLoadRepository(mock_session)

        load = make_load()

        # Mock existing check - load exists
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_existing_result)
        mock_session.merge = AsyncMock()
        mock_session.flush = AsyncMock()

        result = await repo.save(load)
        assert result.load_id == "load-1"
        mock_session.merge.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_state(self):
        """Test update_state transitions load state."""
        mock_session = AsyncMock()
        repo = SqlAlchemyLoadRepository(mock_session)

        load = make_load(current_state=LoadState.DISPATCHED)

        mock_result = MagicMock()
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
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        result = await repo.update_state("load-1", LoadState.ON_ROUTE_TO_DELIVERY)
        assert result.load_id == "load-1"

    @pytest.mark.asyncio
    async def test_update_eta(self):
        """Test update_eta updates load ETA."""
        mock_session = AsyncMock()
        repo = SqlAlchemyLoadRepository(mock_session)

        mock_result = MagicMock()
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
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        result = await repo.update_eta("load-1", "2024-06-01T12:00:00Z")
        assert result.load_id == "load-1"


# --- SqlAlchemyEventRepository Async Method Tests ---

class TestSqlAlchemyEventRepositoryAsync:
    """Tests for SqlAlchemyEventRepository async methods."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Test get_by_id returns event when found."""
        mock_session = AsyncMock()
        repo = SqlAlchemyEventRepository(mock_session)

        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.event_id = "evt-1"
        mock_model.event_type = "inbound_communication"
        mock_model.load_id = "load-1"
        mock_model.customer_id = "customer_a"
        mock_model.occurred_at = "2024-01-01T00:00:00Z"
        mock_model.event_data = {}
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute = AsyncMock(return_value=mock_result)

        event = await repo.get_by_id("evt-1")
        assert event.event_id == "evt-1"
        assert event.event_type == EventType.INBOUND_COMMUNICATION

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test get_by_id raises LoadNotFoundError when not found."""
        mock_session = AsyncMock()
        repo = SqlAlchemyEventRepository(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(LoadNotFoundError):
            await repo.get_by_id("evt-nonexistent")

    @pytest.mark.asyncio
    async def test_get_by_load_id(self):
        """Test get_by_load_id returns list of events."""
        mock_session = AsyncMock()
        repo = SqlAlchemyEventRepository(mock_session)

        mock_model = MagicMock()
        mock_model.event_id = "evt-1"
        mock_model.event_type = "inbound_communication"
        mock_model.load_id = "load-1"
        mock_model.customer_id = "customer_a"
        mock_model.occurred_at = "2024-01-01T00:00:00Z"
        mock_model.event_data = {}

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        events = await repo.get_by_load_id("load-1")
        assert len(events) == 1
        assert events[0].event_id == "evt-1"

    @pytest.mark.asyncio
    async def test_save(self):
        """Test save adds event."""
        mock_session = AsyncMock()
        repo = SqlAlchemyEventRepository(mock_session)

        event = make_event()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        result = await repo.save(event)
        assert result.event_id == "evt-1"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_processed(self):
        """Test mark_processed updates event status."""
        mock_session = AsyncMock()
        repo = SqlAlchemyEventRepository(mock_session)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        await repo.mark_processed("evt-1")
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()


# --- SqlAlchemyToolCallRepository Async Method Tests ---

class TestSqlAlchemyToolCallRepositoryAsync:
    """Tests for SqlAlchemyToolCallRepository async methods."""

    @pytest.mark.asyncio
    async def test_save(self):
        """Test save adds tool call."""
        mock_session = AsyncMock()
        repo = SqlAlchemyToolCallRepository(mock_session)

        tc = make_tool_call()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        result = await repo.save(tc)
        assert result.tool_call_id == "tc-1"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_event_id(self):
        """Test get_by_event_id returns list of tool calls."""
        mock_session = AsyncMock()
        repo = SqlAlchemyToolCallRepository(mock_session)

        mock_model = MagicMock()
        mock_model.tool_call_id = "tc-1"
        mock_model.event_id = "evt-1"
        mock_model.load_id = "load-1"
        mock_model.tool = "send_sms"
        mock_model.arguments = {"to": "+1234567890"}
        mock_model.result = {"status": "sent"}

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        tcs = await repo.get_by_event_id("evt-1")
        assert len(tcs) == 1
        assert tcs[0].tool == "send_sms"

    @pytest.mark.asyncio
    async def test_get_by_load_id(self):
        """Test get_by_load_id returns list of tool calls."""
        mock_session = AsyncMock()
        repo = SqlAlchemyToolCallRepository(mock_session)

        mock_model = MagicMock()
        mock_model.tool_call_id = "tc-1"
        mock_model.event_id = "evt-1"
        mock_model.load_id = "load-1"
        mock_model.tool = "send_sms"
        mock_model.arguments = {}
        mock_model.result = {}

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        tcs = await repo.get_by_load_id("load-1")
        assert len(tcs) == 1


# --- SqlAlchemyAgentRunRepository Async Method Tests ---

class TestSqlAlchemyAgentRunRepositoryAsync:
    """Tests for SqlAlchemyAgentRunRepository async methods."""

    @pytest.mark.asyncio
    async def test_save(self):
        """Test save adds agent run."""
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)

        run = make_agent_run()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        result = await repo.save(run)
        assert result.run_id == run.run_id
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Test get_by_id returns agent run when found."""
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)

        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.run_id = uuid.uuid4()
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
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute = AsyncMock(return_value=mock_result)

        run = await repo.get_by_id(str(mock_model.run_id))
        assert run.workflow == "delivery_eta_checkpoint"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test get_by_id raises LoadNotFoundError when not found."""
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(LoadNotFoundError):
            await repo.get_by_id(str(uuid.uuid4()))

    @pytest.mark.asyncio
    async def test_get_by_load_id(self):
        """Test get_by_load_id returns list of agent runs."""
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)

        mock_model = MagicMock()
        mock_model.run_id = uuid.uuid4()
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

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        runs = await repo.get_by_load_id("load-1")
        assert len(runs) == 1

    @pytest.mark.asyncio
    async def test_update_status(self):
        """Test update_status updates agent run status."""
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        await repo.update_status(str(uuid.uuid4()), "completed")
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_with_error(self):
        """Test update_status with error message."""
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        await repo.update_status(str(uuid.uuid4()), "failed", error="Something went wrong")
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_runs(self):
        """Test get_active_runs returns running agent runs."""
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)

        mock_model = MagicMock()
        mock_model.run_id = uuid.uuid4()
        mock_model.event_id = "evt-1"
        mock_model.load_id = "load-1"
        mock_model.customer_id = "customer_a"
        mock_model.workflow = "delivery_eta_checkpoint"
        mock_model.sop_branch = None
        mock_model.customer_rules_applied = []
        mock_model.tool_calls = []
        mock_model.memory_operations = []
        mock_model.state_before = None
        mock_model.state_after = None
        mock_model.status = "running"
        mock_model.error = None
        mock_model.trace_id = None
        mock_model.started_at = datetime.now(timezone.utc)
        mock_model.completed_at = None

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        runs = await repo.get_active_runs()
        assert len(runs) == 1

    @pytest.mark.asyncio
    async def test_get_recent_runs(self):
        """Test get_recent_runs returns recent agent runs."""
        mock_session = AsyncMock()
        repo = SqlAlchemyAgentRunRepository(mock_session)

        mock_model = MagicMock()
        mock_model.run_id = uuid.uuid4()
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

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        runs = await repo.get_recent_runs()
        assert len(runs) == 1


# --- SqlAlchemyMemoryRepository Async Method Tests ---

class TestSqlAlchemyMemoryRepositoryAsync:
    """Tests for SqlAlchemyMemoryRepository async methods."""

    @pytest.mark.asyncio
    async def test_add(self):
        """Test add creates a memory entry."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        memory_id = await repo.add(
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-1",
            content="Driver arrived at delivery",
            tags=["arrival"],
            confidence=0.9,
        )
        assert memory_id is not None
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_with_expires_at(self):
        """Test add with expires_at creates a memory entry."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        memory_id = await repo.add(
            memory_type=MemoryType.STM,
            scope=MemoryScope.LOAD,
            scope_id="load-1",
            content="Short term memory",
            expires_at="2024-12-31T23:59:59Z",
        )
        assert memory_id is not None

    @pytest.mark.asyncio
    async def test_retrieve(self):
        """Test retrieve returns memories."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)

        mock_model = MagicMock()
        mock_model.id = uuid.uuid4()
        mock_model.memory_type = "episodic"
        mock_model.scope = "load"
        mock_model.scope_id = "load-1"
        mock_model.content = "Driver arrived"
        mock_model.summary = None
        mock_model.tags = ["arrival"]
        mock_model.source_event_ids = []
        mock_model.confidence = 0.9
        mock_model.relevance_score = 0.8
        mock_model.access_count = 5
        mock_model.content_type = "fact"
        mock_model.created_at = datetime.now(timezone.utc)
        mock_model.updated_at = None
        mock_model.expires_at = None

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        memories = await repo.retrieve(
            scope=MemoryScope.LOAD,
            scope_id="load-1",
        )
        assert len(memories) == 1
        assert memories[0]["content"] == "Driver arrived"

    @pytest.mark.asyncio
    async def test_retrieve_with_memory_type(self):
        """Test retrieve with memory type filter."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        memories = await repo.retrieve(
            scope=MemoryScope.LOAD,
            scope_id="load-1",
            memory_type=MemoryType.EPISODIC,
        )
        assert len(memories) == 0

    @pytest.mark.asyncio
    async def test_update(self):
        """Test update modifies a memory entry."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        # Use a valid UUID format for memory_id
        valid_uuid = str(uuid.uuid4())
        await repo.update(valid_uuid, content="Updated content", confidence=0.95)
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete removes a memory entry."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        # Use a valid UUID format for memory_id
        valid_uuid = str(uuid.uuid4())
        await repo.delete(valid_uuid)
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test get_metrics returns memory metrics."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)

        mock_model = MagicMock()
        mock_model.memory_type = "episodic"
        mock_model.confidence = 0.9
        mock_model.relevance_score = 0.8
        mock_model.access_count = 5

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        metrics = await repo.get_metrics(scope=MemoryScope.LOAD, scope_id="load-1")
        assert metrics["total_memories"] == 1
        assert metrics["avg_confidence"] == 0.9
        assert metrics["avg_relevance"] == 0.8
        assert metrics["total_access_count"] == 5

    @pytest.mark.asyncio
    async def test_get_metrics_empty(self):
        """Test get_metrics with no memories."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        metrics = await repo.get_metrics(scope=MemoryScope.LOAD, scope_id="load-1")
        assert metrics["total_memories"] == 0
        assert metrics["avg_confidence"] == 0
        assert metrics["avg_relevance"] == 0

    @pytest.mark.asyncio
    async def test_run_maintenance(self):
        """Test run_maintenance deletes expired memories."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        await repo.run_maintenance()
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize(self):
        """Test summarize creates a summary and archives originals."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)

        mock_model = MagicMock()
        mock_model.id = uuid.uuid4()
        mock_model.content = "Memory content 1"

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        summary_id = await repo.summarize(
            scope=MemoryScope.LOAD,
            scope_id="load-1",
            memory_type=MemoryType.EPISODIC,
        )
        assert summary_id is not None

    @pytest.mark.asyncio
    async def test_summarize_empty(self):
        """Test summarize with no memories returns empty string."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        summary_id = await repo.summarize(
            scope=MemoryScope.LOAD,
            scope_id="load-1",
            memory_type=MemoryType.EPISODIC,
        )
        assert summary_id == ""

    @pytest.mark.asyncio
    async def test_filter(self):
        """Test filter removes low-relevance memories."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)

        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        removed = await repo.filter(
            scope=MemoryScope.LOAD,
            scope_id="load-1",
            memory_type=MemoryType.STM,
            relevance_threshold=0.5,
        )
        assert removed == 3

    @pytest.mark.asyncio
    async def test_filter_memories(self):
        """Test filter_memories removes low-relevance memories."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)

        mock_result = MagicMock()
        mock_result.rowcount = 2
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        result = await repo.filter_memories(
            memory_type=MemoryType.STM,
            scope_id="load-1",
            filter_criteria="low_relevance",
            threshold=0.3,
        )
        assert result["removed"] == 2
        assert result["criteria"] == "low_relevance"
        assert result["threshold"] == 0.3

    @pytest.mark.asyncio
    async def test_get_stm_token_count(self):
        """Test get_stm_token_count returns approximate token count."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryRepository(mock_session)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["Short memory", "A longer memory content here"]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        token_count = await repo.get_stm_token_count(
            scope=MemoryScope.LOAD,
            scope_id="load-1",
        )
        # ~4 chars per token
        assert token_count > 0


# --- SqlAlchemyMemoryOperationLogRepository Async Method Tests ---

class TestSqlAlchemyMemoryOperationLogRepositoryAsync:
    """Tests for SqlAlchemyMemoryOperationLogRepository async methods."""

    @pytest.mark.asyncio
    async def test_save(self):
        """Test save adds a memory operation log."""
        mock_session = AsyncMock()
        repo = SqlAlchemyMemoryOperationLogRepository(mock_session)

        log = MemoryOperationLog(
            operation_id="op-1",
            event_id="evt-1",
            load_id="load-1",
            operation=MemoryOperation.ADD,
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-1",
            content="Added memory",
            result={"status": "success"},
        )
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        result = await repo.save(log)
        assert result.operation_id == "op-1"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_load_id(self):
        """Test get_by_load_id returns list of memory operation logs."""
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
        mock_model.content = "Added memory"
        mock_model.result = {"status": "success"}

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_model]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        logs = await repo.get_by_load_id("load-1")
        assert len(logs) == 1
        assert logs[0].operation_id == "op-1"