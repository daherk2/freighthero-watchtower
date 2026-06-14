"""Database models and session management for FreightHero Watchtower."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    JSON,
    Text,
    Index,
    text,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Vector import for pgvector (must be before model definitions)
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback for when pgvector is not installed (e.g., SQLite for testing)
    Vector = lambda dim: JSON  # type: ignore

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    MemoryOperation,
    MemoryScope,
    MemoryType,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


# --- Database Models ---


class LoadModel(Base):
    """SQLAlchemy model for loads."""

    __tablename__ = "loads"

    load_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    customer_id: Mapped[str] = mapped_column(SAEnum(CustomerId), nullable=False)
    external_load_id: Mapped[str] = mapped_column(String(255), nullable=False)
    po_number: Mapped[str | None] = mapped_column(String(255))
    instructions: Mapped[str | None] = mapped_column(Text)
    load_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    current_state: Mapped[str] = mapped_column(SAEnum(LoadState), nullable=False)
    current_eta_utc: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("ix_loads_customer_id", "customer_id"),)


class EventModel(Base):
    """SQLAlchemy model for events."""

    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    event_type: Mapped[str] = mapped_column(SAEnum(EventType), nullable=False)
    load_id: Mapped[str] = mapped_column(String(255), ForeignKey("loads.load_id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(SAEnum(CustomerId), nullable=False)
    occurred_at: Mapped[str] = mapped_column(String(255), nullable=False)
    event_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (Index("ix_events_load_id", "load_id"),)


class ToolCallModel(Base):
    """SQLAlchemy model for tool call records."""

    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_call_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    load_id: Mapped[str] = mapped_column(String(255), ForeignKey("loads.load_id"), nullable=False)
    tool: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_tool_calls_load_id", "load_id"),
        Index("ix_tool_calls_event_id", "event_id"),
    )


class AgentRunModel(Base):
    """SQLAlchemy model for agent runs."""

    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    load_id: Mapped[str] = mapped_column(String(255), ForeignKey("loads.load_id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(SAEnum(CustomerId), nullable=False)
    workflow: Mapped[str] = mapped_column(String(100), nullable=False)
    sop_branch: Mapped[str | None] = mapped_column(String(100))
    customer_rules_applied: Mapped[dict] = mapped_column(JSON, default=list)
    tool_calls: Mapped[dict] = mapped_column(JSON, default=list)
    memory_operations: Mapped[dict] = mapped_column(JSON, default=list)
    state_before: Mapped[str | None] = mapped_column(SAEnum(LoadState))
    state_after: Mapped[str | None] = mapped_column(SAEnum(LoadState))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    error: Mapped[str | None] = mapped_column(Text)
    trace_id: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_agent_runs_load_id", "load_id"),
        Index("ix_agent_runs_status", "status"),
    )


class TimerModel(Base):
    """SQLAlchemy model for scheduled timers."""

    __tablename__ = "timers"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timer_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    load_id: Mapped[str] = mapped_column(String(255), ForeignKey("loads.load_id"), nullable=False)
    timer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    fire_at_utc: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_timers_load_id", "load_id"),)


class LTMModel(Base):
    """SQLAlchemy model for long-term memory (episodic, semantic, procedural)."""

    __tablename__ = "ltm_memory"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_type: Mapped[str] = mapped_column(SAEnum(MemoryType), nullable=False)
    scope: Mapped[str] = mapped_column(SAEnum(MemoryScope), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[Any] = mapped_column(Vector(1536), nullable=True)  # pgvector
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    source_event_ids: Mapped[dict] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(50), default="fact")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_ltm_memory_scope", "scope", "scope_id"),
        Index("ix_ltm_memory_type", "memory_type"),
    )


class MemoryOperationLogModel(Base):
    """SQLAlchemy model for memory operation logs."""

    __tablename__ = "memory_operation_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    load_id: Mapped[str] = mapped_column(String(255), ForeignKey("loads.load_id"), nullable=False)
    operation: Mapped[str] = mapped_column(SAEnum(MemoryOperation), nullable=False)
    memory_type: Mapped[str] = mapped_column(SAEnum(MemoryType), nullable=False)
    scope: Mapped[str] = mapped_column(SAEnum(MemoryScope), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (Index("ix_memory_ops_load_id", "load_id"),)


# --- Database Session Management ---

class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str):
        # Import asyncpg explicitly to ensure it's available
        import asyncpg  # noqa: F401
        
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def create_tables(self):
        """Create all database tables (preserves existing data)."""
        async with self.engine.begin() as conn:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all database tables (for testing)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncSession:
        """Get an async database session."""
        async with self.async_session() as session:
            yield session

    async def close(self):
        """Close the database engine."""
        await self.engine.dispose()