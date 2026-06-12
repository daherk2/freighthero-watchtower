"""Domain events for FreightHero Watchtower."""

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    MemoryOperation,
    MemoryScope,
    MemoryType,
)


class DomainEvent:
    """Base domain event."""

    event_type: str = "domain_event"


class LoadCreatedEvent(DomainEvent):
    """Event raised when a load is created."""

    event_type: str = "load_created"
    load_id: str
    customer_id: CustomerId
    initial_state: LoadState


class LoadStateChangedEvent(DomainEvent):
    """Event raised when a load's state changes."""

    event_type: str = "load_state_changed"
    load_id: str
    previous_state: LoadState
    new_state: LoadState
    reason: str


class EventEnqueuedEvent(DomainEvent):
    """Event raised when an inbound event is enqueued."""

    event_type: str = "event_enqueued"
    event_id: str
    load_id: str
    event_type_enum: EventType


class AgentRunStartedEvent(DomainEvent):
    """Event raised when an agent run starts."""

    event_type: str = "agent_run_started"
    run_id: str
    event_id: str
    load_id: str
    workflow: str


class AgentRunCompletedEvent(DomainEvent):
    """Event raised when an agent run completes."""

    event_type: str = "agent_run_completed"
    run_id: str
    event_id: str
    load_id: str
    sop_branch: str
    tool_calls_count: int
    memory_operations_count: int
    state_before: LoadState | None
    state_after: LoadState | None


class ToolCallRecordedEvent(DomainEvent):
    """Event raised when a tool call is recorded."""

    event_type: str = "tool_call_recorded"
    tool_call_id: str
    event_id: str
    load_id: str
    tool: str


class MemoryOperationRecordedEvent(DomainEvent):
    """Event raised when a memory operation is recorded."""

    event_type: str = "memory_operation_recorded"
    operation_id: str
    event_id: str
    load_id: str
    operation: MemoryOperation
    memory_type: MemoryType
    scope: MemoryScope
    scope_id: str


class TimerCreatedEvent(DomainEvent):
    """Event raised when a follow-up timer is created."""

    event_type: str = "timer_created"
    timer_id: str
    load_id: str
    timer_type: str
    fire_at_utc: str
    reason: str


class TimerCancelledEvent(DomainEvent):
    """Event raised when a timer is cancelled."""

    event_type: str = "timer_cancelled"
    timer_id: str
    load_id: str