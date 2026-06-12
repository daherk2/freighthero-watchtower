"""Domain models for FreightHero Watchtower."""

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    MemoryOperation,
    MemoryScope,
    MemoryType,
    TaskInstructionType,
    TaskSource,
)
from src.domain.value_objects import (
    Attachment,
    Company,
    InboundCommunication,
    LoadUpdate,
    PersonContact,
    Stop,
    TrackingPing,
)


class Load(BaseModel):
    """Aggregate root representing a freight load."""

    load_id: str
    customer_id: CustomerId
    external_load_id: str
    po_number: str | None = None
    instructions: str | None = None
    load_data: dict = Field(default_factory=dict)
    companies: dict[str, Company] = Field(default_factory=dict)
    contacts: dict[str, PersonContact | None] = Field(default_factory=dict)
    stops: list[Stop] = Field(default_factory=list)
    current_state: LoadState = LoadState.ON_ROUTE_TO_DELIVERY
    current_eta_utc: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def delivery_stop(self) -> Stop | None:
        """Get the delivery stop."""
        return next((s for s in self.stops if s.type == "delivery"), None)

    @property
    def pickup_stop(self) -> Stop | None:
        """Get the pickup stop."""
        return next((s for s in self.stops if s.type == "pickup"), None)

    @property
    def driver(self) -> PersonContact | None:
        """Get the driver contact."""
        return self.contacts.get("driver")

    @property
    def dispatcher(self) -> PersonContact | None:
        """Get the dispatcher contact."""
        return self.contacts.get("dispatcher")

    @property
    def broker(self) -> PersonContact | None:
        """Get the broker contact."""
        return self.contacts.get("broker")

    def transition_to(self, new_state: LoadState, reason: str = "") -> None:
        """Transition to a new load state."""
        valid_transitions = {
            LoadState.DISPATCHED: [LoadState.ON_ROUTE_TO_DELIVERY],
            LoadState.ON_ROUTE_TO_DELIVERY: [LoadState.AT_DELIVERY, LoadState.CONFIRM_DELIVERY],
            LoadState.AT_DELIVERY: [LoadState.DELIVERED, LoadState.ON_ROUTE_TO_DELIVERY, LoadState.CONFIRM_DELIVERY],
            LoadState.CONFIRM_DELIVERY: [LoadState.DELIVERED, LoadState.POD_COLLECTED],
            LoadState.DELIVERED: [LoadState.POD_COLLECTED],
            LoadState.POD_COLLECTED: [],
        }
        allowed = valid_transitions.get(self.current_state, [])
        if new_state not in allowed and new_state != self.current_state:
            from src.domain.exceptions import InvalidStateTransitionError

            raise InvalidStateTransitionError(self.current_state, new_state, self.load_id)
        self.current_state = new_state
        self.updated_at = datetime.now(timezone.utc)


class Event(BaseModel):
    """Base class for all inbound events."""

    event_id: str
    event_type: EventType
    load_id: str
    customer_id: CustomerId
    occurred_at: str
    event_data: dict = Field(default_factory=dict)
    processed_at: datetime | None = None
    processing_status: str = "pending"


class InboundCommunicationEvent(Event):
    """An inbound communication event (SMS or email)."""

    event_type: EventType = EventType.INBOUND_COMMUNICATION
    inbound_communication: InboundCommunication


class TrackingEvent(Event):
    """A tracking ping event."""

    event_type: EventType = EventType.TRACKING
    tracking: TrackingPing


class LoadUpdateEvent(Event):
    """A load update event."""

    event_type: EventType = EventType.LOAD_UPDATE
    load_update: LoadUpdate


class TimerCallbackEvent(Event):
    """A timer callback event."""

    event_type: EventType = EventType.TIMER_CALLBACK
    timer_id: str
    timer_type: str
    reason: str


class TaskSubmission(BaseModel):
    """A workflow task submission."""

    task_uuid: str
    load_id: str
    customer_id: CustomerId
    task_instruction_type: TaskInstructionType
    requested_at: str
    source: TaskSource = TaskSource.API
    payload: dict | None = None


class ToolCall(BaseModel):
    """A tool call made by the agent."""

    tool_call_id: str = Field(default_factory=lambda: str(uuid4()))
    event_id: str
    load_id: str
    tool: str
    arguments: dict = Field(default_factory=dict)
    result: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryOperationLog(BaseModel):
    """A log of a memory operation."""

    operation_id: str = Field(default_factory=lambda: str(uuid4()))
    event_id: str
    load_id: str
    operation: MemoryOperation
    memory_type: MemoryType
    scope: MemoryScope
    scope_id: str
    content: str | None = None
    result: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentRun(BaseModel):
    """A record of a complete agent run."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    event_id: str
    load_id: str
    customer_id: CustomerId
    workflow: str
    sop_branch: str | None = None
    customer_rules_applied: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    memory_operations: list[MemoryOperationLog] = Field(default_factory=list)
    state_before: LoadState | None = None
    state_after: LoadState | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    status: str = "pending"
    error: str | None = None
    trace_id: str | None = None