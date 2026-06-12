"""Domain enums for FreightHero Watchtower."""

from enum import Enum


class LoadState(str, Enum):
    """Load milestone states as defined in the challenge schema."""
    DISPATCHED = "dispatched"
    ON_ROUTE_TO_DELIVERY = "on_route_to_delivery"
    AT_DELIVERY = "at_delivery"
    CONFIRM_DELIVERY = "confirm_delivery"
    DELIVERED = "delivered"
    POD_COLLECTED = "pod_collected"


class CustomerId(str, Enum):
    """Supported customer identifiers."""
    CUSTOMER_A = "customer_a"
    CUSTOMER_B = "customer_b"
    CUSTOMER_C = "customer_c"


class EventType(str, Enum):
    """Types of inbound events."""
    INBOUND_COMMUNICATION = "inbound_communication"
    TRACKING = "tracking"
    LOAD_UPDATE = "load_update"
    TIMER_CALLBACK = "timer_callback"


class TaskInstructionType(str, Enum):
    """Workflow task types."""
    DELIVERY_ETA_CHECKPOINT = "delivery_eta_checkpoint"
    CONFIRM_DELIVERY = "confirm_delivery"


class Channel(str, Enum):
    """Communication channels."""
    SMS = "sms"
    EMAIL = "email"


class SenderType(str, Enum):
    """Types of message senders."""
    DRIVER = "driver"
    DISPATCHER = "dispatcher"
    CARRIER = "carrier"
    BROKER = "broker"
    SHIPPER = "shipper"
    HERO = "hero"
    TOOL = "tool"
    OTHER = "other"


class RecipientType(str, Enum):
    """Types of message recipients."""
    DRIVER = "driver"
    DISPATCHER = "dispatcher"
    CARRIER_TEAM = "carrier_team"
    MAIN_THREAD = "main_thread"


class AudienceType(str, Enum):
    """Slack audience types."""
    INTERNAL = "internal"
    BROKER = "broker"
    CUSTOMER = "customer"


class AttachmentCategory(str, Enum):
    """Attachment classification categories."""
    DOCUMENT_POD = "document_pod"
    LUMPER_RECEIPT = "lumper_receipt"
    PHOTO_UNLOADED = "photo_unloaded"
    OTHER_DOCUMENT = "other_document"
    UNREADABLE = "unreadable"


class TimerType(str, Enum):
    """Types of follow-up timers."""
    ETA_FOLLOWUP = "eta_followup"
    POD_FOLLOWUP = "pod_followup"
    DELIVERY_STATUS_FOLLOWUP = "delivery_status_followup"
    ATTACHMENT_CLARIFICATION = "attachment_clarification"


class TaskType(str, Enum):
    """Types of human follow-up tasks."""
    MISSING_LOAD_INFO = "missing_load_info"
    POD_REVIEW = "pod_review"
    LUMPER_REVIEW = "lumper_review"
    MANUAL_FOLLOWUP = "manual_followup"
    OTHER = "other"


class IssueType(str, Enum):
    """Types of operational issues."""
    EQUIPMENT_FAILURE = "equipment_failure"
    ACCIDENT = "accident"
    FACILITY_ACCESS = "facility_access"
    FREIGHT_DAMAGE = "freight_damage"
    OTHER = "other"


class SOPBranch(str, Enum):
    """SOP branch identifiers for ETA Checkpoint workflow."""
    TRACKING_PING = "tracking_ping"
    ARRIVAL_CONFIRMATION = "arrival_confirmation"
    DRIVER_PROVIDES_ETA = "driver_provides_eta"
    LOAD_INFORMATION_QUESTION = "load_information_question"
    OPERATIONAL_ISSUE = "operational_issue"
    BROKER_MESSAGES = "broker_messages"
    NO_ACTION = "no_action"


class ConfirmDeliveryBranch(str, Enum):
    """SOP branch identifiers for Confirm Delivery workflow."""
    FIRST_ARRIVAL_CONTACT = "first_arrival_contact"
    POD_DOCUMENT = "pod_document"
    LUMPER_RECEIPT = "lumper_receipt"
    OTHER_ATTACHMENT = "other_attachment"
    UNLOADING_STARTED = "unloading_started"
    UNLOADING_NOT_STARTED = "unloading_not_started"
    DELIVERED_WITHOUT_POD = "delivered_without_pod"
    BROKER_MESSAGES = "broker_messages"
    OPERATIONAL_ISSUE = "operational_issue"
    NO_ACTION = "no_action"


class MemoryType(str, Enum):
    """Types of agentic memory."""
    STM = "stm"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryScope(str, Enum):
    """Scopes for memory operations."""
    CUSTOMER = "customer"
    LOAD = "load"
    DRIVER = "driver"
    CARRIER = "carrier"
    GLOBAL = "global"


class MemoryOperation(str, Enum):
    """Memory operation types."""
    ADD = "add"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DELETE = "delete"
    SUMMARIZE = "summarize"
    FILTER = "filter"


class AppointmentType(str, Enum):
    """Appointment schedule types."""
    FIXED = "fixed"
    WINDOW = "window"
    FCFS = "fcfs"


class StopType(str, Enum):
    """Stop types."""
    PICKUP = "pickup"
    DELIVERY = "delivery"


class TaskSource(str, Enum):
    """Task source types."""
    API = "api"
    OPERATOR = "operator"
    SYSTEM = "system"