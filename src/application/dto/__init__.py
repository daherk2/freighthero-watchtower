"""Application DTOs (Data Transfer Objects) for FreightHero Watchtower.

These are the request/response schemas for the API layer.
"""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from src.domain.enums import (
    AttachmentCategory,
    Channel,
    CustomerId,
    EventType,
    LoadState,
    MemoryOperation,
    MemoryScope,
    MemoryType,
    SenderType,
    TaskInstructionType,
    TaskSource,
)


# --- Request DTOs ---


class CreateLoadRequest(BaseModel):
    """Request to create/seed a load."""

    load_id: str | None = None  # Auto-generated if not provided
    customer_id: CustomerId
    external_load_id: str = ""
    po_number: str | None = None
    instructions: str | None = None
    load_data: dict = Field(default_factory=dict)
    initial_state: LoadState | None = LoadState.DISPATCHED
    current_eta_utc: str | None = None
    run_pipeline: bool = True  # Automatically trigger pipeline after creation


class CreateLoadResponse(BaseModel):
    """Response after creating a load."""

    load_id: str
    customer_id: CustomerId
    external_load_id: str = ""
    current_state: LoadState
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pipeline_triggered: bool = False
    pipeline_workflow: str | None = None
    pipeline_status: str | None = None


class SubmitTaskRequest(BaseModel):
    """Request to submit a workflow task."""

    task_uuid: str = Field(..., min_length=1)
    load_id: str = Field(..., min_length=1)
    customer_id: CustomerId
    task_instruction_type: TaskInstructionType
    requested_at: str
    source: TaskSource = TaskSource.API
    payload: dict | None = None


class SubmitTaskResponse(BaseModel):
    """Response after submitting a task."""

    task_uuid: str
    load_id: str
    task_instruction_type: TaskInstructionType
    status: str = "enqueued"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InboundCommunicationRequest(BaseModel):
    """Request to enqueue an inbound communication event."""

    event_id: str = Field(..., min_length=1)
    event_type: EventType = EventType.INBOUND_COMMUNICATION
    load_id: str = Field(..., min_length=1)
    customer_id: CustomerId
    occurred_at: str
    inbound_communication: dict


class TrackingEventRequest(BaseModel):
    """Request to enqueue a tracking event."""

    event_id: str = Field(..., min_length=1)
    event_type: EventType = EventType.TRACKING
    load_id: str = Field(..., min_length=1)
    customer_id: CustomerId
    occurred_at: str
    tracking: dict


class LoadUpdateEventRequest(BaseModel):
    """Request to enqueue a load update event."""

    event_id: str = Field(..., min_length=1)
    event_type: EventType = EventType.LOAD_UPDATE
    load_id: str = Field(..., min_length=1)
    customer_id: CustomerId
    occurred_at: str
    load_update: dict


class EventResponse(BaseModel):
    """Response after enqueuing an event."""

    event_id: str
    load_id: str = ""
    event_type: EventType = EventType.INBOUND_COMMUNICATION
    status: str = "enqueued"
    workflow: str = ""
    timestamp: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Memory Tool DTOs ---


class MemoryAddRequest(BaseModel):
    """Request to add a memory entry."""

    memory_type: MemoryType
    scope: MemoryScope
    scope_id: str
    content: str
    content_type: str = "fact"
    tags: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    expires_at: str | None = None


class MemoryAddResponse(BaseModel):
    """Response after adding a memory entry."""

    ok: bool = True
    memory_id: str
    memory_type: MemoryType
    scope: MemoryScope
    scope_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryRetrieveRequest(BaseModel):
    """Request to retrieve memories."""

    query: str
    memory_types: list[MemoryType] = Field(
        default_factory=lambda: [MemoryType.STM, MemoryType.EPISODIC, MemoryType.SEMANTIC]
    )
    scope: MemoryScope | None = None
    scope_id: str | None = None
    limit: int = 10
    min_relevance: float = 0.5


class MemoryRetrieveResponse(BaseModel):
    """Response after retrieving memories."""

    ok: bool = True
    memories: list[dict] = Field(default_factory=list)
    total_count: int = 0
    retrieval_method: str = "hybrid"


class MemoryUpdateRequest(BaseModel):
    """Request to update a memory entry."""

    memory_id: str
    content: str | None = None
    confidence: float | None = None
    relevance_score: float | None = None
    expires_at: str | None = None


class MemoryUpdateResponse(BaseModel):
    """Response after updating a memory entry."""

    ok: bool = True
    memory_id: str
    updated_fields: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryDeleteRequest(BaseModel):
    """Request to delete memory entries."""

    memory_id: str | None = None
    memory_type: MemoryType | None = None
    scope: MemoryScope | None = None
    scope_id: str | None = None
    reason: str = ""


class MemoryDeleteResponse(BaseModel):
    """Response after deleting memory entries."""

    ok: bool = True
    deleted_count: int = 0
    deleted_memory_ids: list[str] = Field(default_factory=list)


class MemorySummarizeRequest(BaseModel):
    """Request to summarize memory context."""

    memory_type: MemoryType = MemoryType.STM
    scope_id: str = ""
    strategy: str = "compress_older"
    max_tokens: int | None = None
    preserve_recent_n: int = 5


class MemorySummarizeResponse(BaseModel):
    """Response after summarizing memory context."""

    ok: bool = True
    original_token_count: int = 0
    summarized_token_count: int = 0
    reduction_percentage: float = 0.0
    summary_id: str = Field(default_factory=lambda: str(uuid4()))
    items_summarized: int = 0
    items_preserved: int = 0


class MemoryFilterRequest(BaseModel):
    """Request to filter memory entries."""

    memory_type: MemoryType = MemoryType.STM
    scope_id: str = ""
    filter_criteria: str = "low_relevance"
    threshold: float | None = None


class MemoryFilterResponse(BaseModel):
    """Response after filtering memory entries."""

    ok: bool = True
    filtered_count: int = 0
    remaining_count: int = 0
    filter_criteria: str = ""


# --- Monitoring Dashboard DTOs ---


class AgentRunSummary(BaseModel):
    """Summary of an agent run for the dashboard."""

    run_id: str
    event_id: str
    load_id: str
    customer_id: CustomerId
    workflow: str
    sop_branch: str | None = None
    tool_calls_count: int = 0
    memory_operations_count: int = 0
    state_before: LoadState | None = None
    state_after: LoadState | None = None
    status: str = "pending"
    started_at: datetime
    completed_at: datetime | None = None
    trace_id: str | None = None


class ToolCallSummary(BaseModel):
    """Summary of a tool call for the dashboard."""

    tool_call_id: str
    event_id: str
    load_id: str
    tool: str
    arguments: dict = Field(default_factory=dict)
    result: dict = Field(default_factory=dict)
    created_at: datetime


class MemoryOperationSummary(BaseModel):
    """Summary of a memory operation for the dashboard."""

    operation_id: str
    event_id: str
    load_id: str
    operation: MemoryOperation
    memory_type: MemoryType
    scope: MemoryScope
    scope_id: str
    content: str | None = None
    created_at: datetime


class StateTransitionSummary(BaseModel):
    """Summary of a state transition for the dashboard."""

    load_id: str
    from_state: LoadState
    to_state: LoadState
    reason: str = ""
    timestamp: datetime | str = ""


class ActiveLoadSummary(BaseModel):
    """Summary of an active load for the dashboard."""

    load_id: str
    customer_id: CustomerId
    external_load_id: str | None = None
    po_number: str | None = None
    current_state: LoadState
    current_eta_utc: str | None = None
    load_data: dict = {}
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None
    last_event_at: datetime | None = None
    last_run_at: datetime | None = None


class ScheduledFollowUp(BaseModel):
    """A scheduled follow-up timer."""

    timer_id: str
    load_id: str
    timer_type: str
    fire_at_utc: str
    reason: str
    status: str = "scheduled"


class FailureSummary(BaseModel):
    """Summary of a failure for the dashboard."""

    run_id: str
    event_id: str
    load_id: str
    error: str
    timestamp: datetime


class MemoryMetrics(BaseModel):
    """Memory system metrics."""

    retrieval_count: int = 0
    memory_growth_rate: float = 0.0
    memory_hit_rate: float = 0.0
    memory_update_rate: int = 0
    memory_delete_rate: int = 0
    context_token_reduction: float = 0.0
    memory_relevance_score: float = 0.0
    stm_utilization: float = 0.0
    ltm_size: int = 0
    memory_operation_latency_ms: float = 0.0