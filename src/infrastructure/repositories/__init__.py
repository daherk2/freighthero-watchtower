"""Infrastructure repository implementations.

These are the concrete implementations of the application port interfaces,
using SQLAlchemy for persistence, Redis for caching, and PGVector for
semantic search.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import select, update, delete, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    MemoryOperation,
    MemoryScope,
    MemoryType,
)
from src.domain.exceptions import (
    LoadNotFoundError,
    MemoryOperationError,
)
from src.domain.models import (
    AgentRun,
    Event,
    Load,
    MemoryOperationLog,
    ToolCall,
)
from src.domain.value_objects import (
    CustomerBehaviorConfig,
    MemoryOperationRecord,
    ToolCallRecord,
)
from src.application.ports import (
    AgentRunRepository,
    EventQueue,
    EventRepository,
    LoadRepository,
    MemoryOperationLogRepository,
    MemoryRepository,
    ToolCallRepository,
)
from src.infrastructure.database import (
    AgentRunModel,
    EventModel,
    LTMModel,
    LoadModel,
    MemoryOperationLogModel,
    TimerModel,
    ToolCallModel,
)


# --- Load Repository ---


class SqlAlchemyLoadRepository(LoadRepository):
    """SQLAlchemy implementation of LoadRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, load_id: str) -> Load:
        result = await self._session.execute(
            select(LoadModel).where(LoadModel.load_id == load_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise LoadNotFoundError(load_id)
        return self._to_domain(model)

    async def get_active_loads(self) -> list[Load]:
        result = await self._session.execute(
            select(LoadModel).where(
                LoadModel.current_state.in_([
                    LoadState.DISPATCHED,
                    LoadState.ON_ROUTE_TO_DELIVERY,
                    LoadState.AT_DELIVERY,
                    LoadState.CONFIRM_DELIVERY,
                ])
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, load: Load) -> Load:
        model = self._to_model(load)
        existing = await self._session.execute(
            select(LoadModel).where(LoadModel.load_id == load.load_id)
        )
        if existing.scalar_one_or_none():
            await self._session.merge(model)
        else:
            self._session.add(model)
        await self._session.flush()
        return load

    async def update_state(self, load_id: str, new_state: LoadState, reason: str = "") -> Load:
        load = await self.get_by_id(load_id)
        load.transition_to(new_state)
        return await self.save(load)

    async def update_eta(self, load_id: str, eta_utc: str, source: str = "") -> Load:
        load = await self.get_by_id(load_id)
        load.current_eta_utc = eta_utc
        return await self.save(load)

    def _to_domain(self, model: LoadModel) -> Load:
        return Load(
            load_id=model.load_id,
            customer_id=CustomerId(model.customer_id),
            external_load_id=model.external_load_id,
            po_number=model.po_number,
            instructions=model.instructions,
            load_data=model.load_data,
            current_state=LoadState(model.current_state),
            current_eta_utc=model.current_eta_utc,
            created_at=model.created_at.isoformat() if model.created_at else None,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
        )

    def _to_model(self, load: Load) -> LoadModel:
        return LoadModel(
            load_id=load.load_id,
            customer_id=load.customer_id,
            external_load_id=load.external_load_id,
            po_number=load.po_number,
            instructions=load.instructions,
            load_data=load.load_data,
            current_state=load.current_state,
            current_eta_utc=load.current_eta_utc,
        )


# --- Event Repository ---


class SqlAlchemyEventRepository(EventRepository):
    """SQLAlchemy implementation of EventRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, event_id: str) -> Event:
        result = await self._session.execute(
            select(EventModel).where(EventModel.event_id == event_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise LoadNotFoundError(event_id)
        return self._to_domain(model)

    async def get_by_load_id(self, load_id: str) -> list[Event]:
        result = await self._session.execute(
            select(EventModel)
            .where(EventModel.load_id == load_id)
            .order_by(EventModel.occurred_at)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, event: Event) -> Event:
        model = self._to_model(event)
        self._session.add(model)
        await self._session.flush()
        return event

    async def mark_processed(self, event_id: str) -> None:
        await self._session.execute(
            update(EventModel)
            .where(EventModel.event_id == event_id)
            .values(processing_status="processed", processed_at=datetime.now(timezone.utc))
        )
        await self._session.flush()

    def _to_domain(self, model: EventModel) -> Event:
        return Event(
            event_id=model.event_id,
            event_type=EventType(model.event_type),
            load_id=model.load_id,
            customer_id=CustomerId(model.customer_id),
            occurred_at=model.occurred_at,
            event_data=model.event_data,
        )

    def _to_model(self, event: Event) -> EventModel:
        return EventModel(
            event_id=event.event_id,
            event_type=event.event_type,
            load_id=event.load_id,
            customer_id=event.customer_id,
            occurred_at=event.occurred_at,
            event_data=event.event_data,
        )


# --- Tool Call Repository ---


class SqlAlchemyToolCallRepository(ToolCallRepository):
    """SQLAlchemy implementation of ToolCallRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, tool_call: ToolCall) -> ToolCall:
        model = ToolCallModel(
            tool_call_id=tool_call.tool_call_id,
            event_id=tool_call.event_id,
            load_id=tool_call.load_id,
            tool=tool_call.tool,
            arguments=tool_call.arguments,
            result=tool_call.result,
        )
        self._session.add(model)
        await self._session.flush()
        return tool_call

    async def get_by_event_id(self, event_id: str) -> list[ToolCall]:
        result = await self._session.execute(
            select(ToolCallModel).where(ToolCallModel.event_id == event_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_load_id(self, load_id: str) -> list[ToolCall]:
        result = await self._session.execute(
            select(ToolCallModel).where(ToolCallModel.load_id == load_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: ToolCallModel) -> ToolCall:
        return ToolCall(
            tool_call_id=model.tool_call_id,
            event_id=model.event_id,
            load_id=model.load_id,
            tool=model.tool,
            arguments=model.arguments,
            result=model.result,
        )


# --- Agent Run Repository ---


class SqlAlchemyAgentRunRepository(AgentRunRepository):
    """SQLAlchemy implementation of AgentRunRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, agent_run: AgentRun) -> AgentRun:
        # Convert ToolCall and MemoryOperationLog objects to dicts for JSON storage
        # Use mode='json' to ensure datetime objects are serialized as ISO strings
        tool_calls_data = [
            tc.model_dump(mode='json') if hasattr(tc, 'model_dump') else tc
            for tc in agent_run.tool_calls
        ]
        memory_ops_data = [
            mo.model_dump(mode='json') if hasattr(mo, 'model_dump') else mo
            for mo in agent_run.memory_operations
        ]
        model = AgentRunModel(
            run_id=uuid.UUID(agent_run.run_id) if agent_run.run_id else uuid.uuid4(),
            event_id=agent_run.event_id,
            load_id=agent_run.load_id,
            customer_id=agent_run.customer_id,
            workflow=agent_run.workflow,
            sop_branch=agent_run.sop_branch,
            customer_rules_applied=agent_run.customer_rules_applied,
            tool_calls=tool_calls_data,
            memory_operations=memory_ops_data,
            state_before=agent_run.state_before,
            state_after=agent_run.state_after,
            status=agent_run.status,
            error=agent_run.error,
            trace_id=agent_run.trace_id,
            started_at=agent_run.started_at,
            completed_at=agent_run.completed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return agent_run

    async def get_by_id(self, run_id: str) -> AgentRun:
        result = await self._session.execute(
            select(AgentRunModel).where(AgentRunModel.run_id == uuid.UUID(run_id))
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise LoadNotFoundError(run_id)
        return self._to_domain(model)

    async def get_by_load_id(self, load_id: str) -> list[AgentRun]:
        result = await self._session.execute(
            select(AgentRunModel)
            .where(AgentRunModel.load_id == load_id)
            .order_by(desc(AgentRunModel.started_at))
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update_status(self, run_id: str, status: str, error: str | None = None) -> None:
        values = {"status": status}
        if status == "completed":
            values["completed_at"] = datetime.now(timezone.utc)
        if error:
            values["error"] = error
        await self._session.execute(
            update(AgentRunModel)
            .where(AgentRunModel.run_id == uuid.UUID(run_id))
            .values(**values)
        )
        await self._session.flush()

    async def get_active_runs(self, limit: int = 100) -> list[AgentRun]:
        result = await self._session.execute(
            select(AgentRunModel)
            .where(AgentRunModel.status == "running")
            .order_by(desc(AgentRunModel.started_at))
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_recent_runs(self, limit: int = 50) -> list[AgentRun]:
        result = await self._session.execute(
            select(AgentRunModel)
            .order_by(desc(AgentRunModel.started_at))
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: AgentRunModel) -> AgentRun:
        return AgentRun(
            run_id=str(model.run_id),
            event_id=model.event_id,
            load_id=model.load_id,
            customer_id=CustomerId(model.customer_id),
            workflow=model.workflow,
            sop_branch=model.sop_branch,
            customer_rules_applied=model.customer_rules_applied or [],
            tool_calls=model.tool_calls or [],
            memory_operations=model.memory_operations or [],
            state_before=LoadState(model.state_before) if model.state_before else None,
            state_after=LoadState(model.state_after) if model.state_after else None,
            status=model.status,
            error=model.error,
            trace_id=model.trace_id,
            started_at=model.started_at.isoformat() if model.started_at else None,
            completed_at=model.completed_at.isoformat() if model.completed_at else None,
        )


# --- Memory Repository ---


class SqlAlchemyMemoryRepository(MemoryRepository):
    """SQLAlchemy + PGVector implementation of MemoryRepository.

    Uses PostgreSQL with PGVector extension for semantic search
    and LangMem for long-term memory management.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(
        self,
        memory_type: MemoryType,
        scope: MemoryScope,
        scope_id: str,
        content: str,
        tags: list[str] | None = None,
        source_event_ids: list[str] | None = None,
        confidence: float = 1.0,
        content_type: str = "fact",
        expires_at: str | None = None,
    ) -> str:
        memory_id = str(uuid.uuid4())
        model = LTMModel(
            id=uuid.UUID(memory_id),
            memory_type=memory_type,
            scope=scope,
            scope_id=scope_id,
            content=content,
            tags=tags or [],
            source_event_ids=source_event_ids or [],
            confidence=confidence,
            content_type=content_type,
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
        )
        self._session.add(model)
        await self._session.flush()
        return memory_id

    async def retrieve(
        self,
        scope: MemoryScope,
        scope_id: str,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict]:
        query = select(LTMModel).where(
            and_(
                LTMModel.scope == scope,
                LTMModel.scope_id == scope_id,
            )
        )
        if memory_type:
            query = query.where(LTMModel.memory_type == memory_type)
        if tags:
            query = query.where(LTMModel.tags.contains(tags))

        query = query.order_by(desc(LTMModel.relevance_score)).limit(limit)
        result = await self._session.execute(query)
        return [self._model_to_dict(m) for m in result.scalars().all()]

    async def update(self, memory_id: str, content: str | None = None, tags: list[str] | None = None, confidence: float | None = None) -> None:
        values = {"updated_at": datetime.now(timezone.utc)}
        if content is not None:
            values["content"] = content
        if tags is not None:
            values["tags"] = tags
        if confidence is not None:
            values["confidence"] = confidence
        values["access_count"] = LTMModel.access_count + 1
        await self._session.execute(
            update(LTMModel).where(LTMModel.id == uuid.UUID(memory_id)).values(**values)
        )
        await self._session.flush()

    async def delete(self, memory_id: str) -> None:
        await self._session.execute(
            delete(LTMModel).where(LTMModel.id == uuid.UUID(memory_id))
        )
        await self._session.flush()

    async def summarize(self, scope: MemoryScope, scope_id: str, memory_type: MemoryType) -> str:
        """Summarize memories of a given type and scope.

        Creates a compressed summary and archives the original memories.
        """
        result = await self._session.execute(
            select(LTMModel).where(
                and_(
                    LTMModel.scope == scope,
                    LTMModel.scope_id == scope_id,
                    LTMModel.memory_type == memory_type,
                )
            )
        )
        memories = result.scalars().all()
        if not memories:
            return ""

        # Combine content for summarization
        combined = "\n".join([m.content for m in memories])
        summary_id = str(uuid.uuid4())
        summary_model = LTMModel(
            id=uuid.UUID(summary_id),
            memory_type=memory_type,
            scope=scope,
            scope_id=scope_id,
            content=f"[SUMMARY] {combined[:500]}...",
            summary=combined,
            tags=["summary", "compressed"],
            source_event_ids=[str(m.id) for m in memories],
            confidence=0.9,
            content_type="summary",
        )
        self._session.add(summary_model)

        # Archive originals
        for m in memories:
            await self._session.delete(m)

        await self._session.flush()
        return summary_id

    async def filter(self, scope: MemoryScope, scope_id: str, memory_type: MemoryType, relevance_threshold: float = 0.5) -> int:
        """Remove memories below the relevance threshold.

        Returns the number of memories removed.
        """
        result = await self._session.execute(
            delete(LTMModel).where(
                and_(
                    LTMModel.scope == scope,
                    LTMModel.scope_id == scope_id,
                    LTMModel.memory_type == memory_type,
                    LTMModel.relevance_score < relevance_threshold,
                )
            )
        )
        await self._session.flush()
        return result.rowcount

    async def filter_memories(
        self,
        memory_type: MemoryType = MemoryType.STM,
        scope_id: str = "",
        filter_criteria: str = "low_relevance",
        threshold: float | None = None,
    ) -> dict:
        """Filter and remove irrelevant memories."""
        scope = MemoryScope.LOAD
        relevance_threshold = threshold if threshold is not None else 0.5
        removed = await self.filter(
            scope=scope,
            scope_id=scope_id,
            memory_type=memory_type,
            relevance_threshold=relevance_threshold,
        )
        return {"removed": removed, "criteria": filter_criteria, "threshold": relevance_threshold}

    async def get_stm_token_count(self, scope: MemoryScope, scope_id: str) -> int:
        """Get approximate token count for STM (short-term memory) entries."""
        result = await self._session.execute(
            select(LTMModel.content).where(
                and_(
                    LTMModel.scope == scope,
                    LTMModel.scope_id == scope_id,
                    LTMModel.memory_type == MemoryType.EPISODIC,
                )
            )
        )
        contents = result.scalars().all()
        # Rough token estimate: ~4 chars per token
        return sum(len(c) // 4 for c in contents)

    async def get_metrics(self, scope: MemoryScope, scope_id: str) -> dict:
        """Get memory metrics for a given scope."""
        result = await self._session.execute(
            select(LTMModel).where(
                and_(
                    LTMModel.scope == scope,
                    LTMModel.scope_id == scope_id,
                )
            )
        )
        memories = result.scalars().all()

        by_type = {}
        for m in memories:
            key = m.memory_type if isinstance(m.memory_type, str) else m.memory_type.value
            by_type[key] = by_type.get(key, 0) + 1

        return {
            "total_memories": len(memories),
            "by_type": by_type,
            "avg_confidence": sum(m.confidence for m in memories) / len(memories) if memories else 0,
            "avg_relevance": sum(m.relevance_score for m in memories) / len(memories) if memories else 0,
            "total_access_count": sum(m.access_count for m in memories),
        }

    async def run_maintenance(self) -> None:
        """Run periodic maintenance: expire old memories, compress, etc."""
        now = datetime.now(timezone.utc)
        # Delete expired memories
        await self._session.execute(
            delete(LTMModel).where(
                and_(
                    LTMModel.expires_at.isnot(None),
                    LTMModel.expires_at < now,
                )
            )
        )
        await self._session.flush()

    def _model_to_dict(self, model: LTMModel) -> dict:
        return {
            "id": str(model.id),
            "memory_type": model.memory_type if isinstance(model.memory_type, str) else model.memory_type.value,
            "scope": model.scope if isinstance(model.scope, str) else model.scope.value,
            "scope_id": model.scope_id,
            "content": model.content,
            "summary": model.summary,
            "tags": model.tags,
            "source_event_ids": model.source_event_ids,
            "confidence": model.confidence,
            "relevance_score": model.relevance_score,
            "access_count": model.access_count,
            "content_type": model.content_type,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            "expires_at": model.expires_at.isoformat() if model.expires_at else None,
        }


# --- Memory Operation Log Repository ---


class SqlAlchemyMemoryOperationLogRepository(MemoryOperationLogRepository):
    """SQLAlchemy implementation of MemoryOperationLogRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, log: MemoryOperationLog) -> MemoryOperationLog:
        model = MemoryOperationLogModel(
            operation_id=log.operation_id,
            event_id=log.event_id,
            load_id=log.load_id,
            operation=log.operation,
            memory_type=log.memory_type,
            scope=log.scope,
            scope_id=log.scope_id,
            content=log.content,
            result=log.result,
        )
        self._session.add(model)
        await self._session.flush()
        return log

    async def get_by_load_id(self, load_id: str) -> list[MemoryOperationLog]:
        result = await self._session.execute(
            select(MemoryOperationLogModel)
            .where(MemoryOperationLogModel.load_id == load_id)
            .order_by(MemoryOperationLogModel.created_at)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: MemoryOperationLogModel) -> MemoryOperationLog:
        return MemoryOperationLog(
            operation_id=model.operation_id,
            event_id=model.event_id,
            load_id=model.load_id,
            operation=model.operation,
            memory_type=model.memory_type,
            scope=model.scope,
            scope_id=model.scope_id,
            content=model.content,
            result=model.result,
        )


# --- Event Queue (Redis-backed) ---


class RedisEventQueue(EventQueue):
    """Redis-backed event queue implementation."""

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._queue_key = "freighthero:events:pending"

    async def enqueue(self, event: Event) -> None:
        import json
        if self._redis is None:
            return  # No-op if Redis not configured
        data = json.dumps({
            "event_id": event.event_id,
            "event_type": event.event_type if isinstance(event.event_type, str) else event.event_type.value,
            "load_id": event.load_id,
            "customer_id": event.customer_id if isinstance(event.customer_id, str) else event.customer_id.value,
            "occurred_at": event.occurred_at,
            "event_data": event.event_data,
        })
        await self._redis.lpush(self._queue_key, data)

    async def dequeue(self) -> Event | None:
        import json
        if self._redis is None:
            return None
        data = await self._redis.brpop(self._queue_key, timeout=1)
        if data is None:
            return None
        parsed = json.loads(data[1])
        return Event(
            event_id=parsed["event_id"],
            event_type=EventType(parsed["event_type"]),
            load_id=parsed["load_id"],
            customer_id=CustomerId(parsed["customer_id"]),
            occurred_at=parsed["occurred_at"],
            event_data=parsed["event_data"],
        )

    async def size(self) -> int:
        if self._redis is None:
            return 0
        return await self._redis.llen(self._queue_key)


# --- Repository Factory Functions ---


def get_load_repository(session: AsyncSession) -> LoadRepository:
    return SqlAlchemyLoadRepository(session)


def get_event_repository(session: AsyncSession) -> EventRepository:
    return SqlAlchemyEventRepository(session)


def get_tool_call_repository(session: AsyncSession) -> ToolCallRepository:
    return SqlAlchemyToolCallRepository(session)


def get_agent_run_repository(session: AsyncSession) -> AgentRunRepository:
    return SqlAlchemyAgentRunRepository(session)


def get_memory_repository(session: AsyncSession) -> MemoryRepository:
    return SqlAlchemyMemoryRepository(session)


def get_memory_operation_log_repository(session: AsyncSession) -> MemoryOperationLogRepository:
    return SqlAlchemyMemoryOperationLogRepository(session)