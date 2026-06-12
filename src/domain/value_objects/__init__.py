"""Domain value objects for FreightHero Watchtower."""

from pydantic import BaseModel, Field

from src.domain.enums import (
    AppointmentType,
    AttachmentCategory,
    Channel,
    CustomerId,
    LoadState,
    MemoryOperation,
    MemoryScope,
    MemoryType,
    RecipientType,
    SenderType,
    StopType,
    TaskInstructionType,
    TaskSource,
)


class Address(BaseModel):
    """Physical address value object."""

    line_1: str
    line_2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str = "US"


class Coordinates(BaseModel):
    """GPS coordinates value object."""

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class Appointment(BaseModel):
    """Delivery/pickup appointment value object."""

    type: AppointmentType
    start_utc: str | None = None
    end_utc: str | None = None
    timezone: str


class PersonContact(BaseModel):
    """Contact information for a person."""

    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    uuid: str | None = None


class Company(BaseModel):
    """Company information value object."""

    name: str
    uuid: str | None = None


class Stop(BaseModel):
    """A pickup or delivery stop."""

    stop_id: str
    type: StopType
    status: str | None = None
    address: Address
    appointment: Appointment
    coordinates: Coordinates
    reference_numbers: dict[str, str] = Field(default_factory=dict)


class Attachment(BaseModel):
    """An attachment with mock classification."""

    attachment_id: str
    file_name: str
    mime_type: str | None = None
    mock_classification: "AttachmentClassification | None" = None


class AttachmentClassification(BaseModel):
    """Mock classification result for an attachment."""

    categories: list[AttachmentCategory]
    description: str | None = None


class InboundCommunication(BaseModel):
    """An inbound communication (SMS or email)."""

    channel: Channel
    sender_type: SenderType
    sender_name: str | None = None
    content: str
    attachments: list[Attachment] = Field(default_factory=list)


class TrackingPing(BaseModel):
    """A GPS tracking ping."""

    tracking_id: str
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    distance_to_delivery_miles: float = Field(ge=0)
    ping_sequence: int = Field(ge=1)
    provider: str | None = None


class LoadUpdate(BaseModel):
    """An update to load data or milestone state."""

    milestone_state: LoadState | None = None
    load_data_patch: dict | None = None
    reason: str | None = None


class ToolCallRecord(BaseModel):
    """A record of a tool call made by the agent."""

    tool_call_id: str
    event_id: str
    load_id: str
    tool: str
    arguments: dict = Field(default_factory=dict)
    result: dict = Field(default_factory=dict)
    created_at: str


class MemoryOperationRecord(BaseModel):
    """A record of a memory operation."""

    operation_id: str
    event_id: str
    load_id: str
    operation: MemoryOperation
    memory_type: MemoryType
    scope: MemoryScope
    scope_id: str
    content: str | None = None
    result: dict = Field(default_factory=dict)
    created_at: str


class CustomerBehaviorConfig(BaseModel):
    """Customer-specific behavior configuration."""

    customer_id: CustomerId
    escalation_channel: str
    missing_load_info_action: str
    pod_validation_type: str
    pod_received_visibility: str
    delivered_without_pod_visibility: str
    delivery_geofence_radius_miles: int
    eta_followup_timer_minutes: int
    lumper_receipt_handling: str
    first_arrival_message: str


class GeofenceStatus(BaseModel):
    """Status of geofence tracking for a load."""

    consecutive_pings_inside: int = 0
    last_ping_inside: bool = False
    last_ping_timestamp: str | None = None


# Resolve forward references
Attachment.model_rebuild()