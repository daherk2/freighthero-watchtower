"""Domain exceptions for FreightHero Watchtower."""


class FreightHeroError(Exception):
    """Base exception for FreightHero domain errors."""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(message)


class LoadNotFoundError(FreightHeroError):
    """Raised when a load is not found."""

    def __init__(self, load_id: str):
        super().__init__(f"Load not found: {load_id}", code="LOAD_NOT_FOUND")
        self.load_id = load_id


class InvalidStateTransitionError(FreightHeroError):
    """Raised when a state transition is invalid."""

    def __init__(self, from_state: str, to_state: str, load_id: str = ""):
        super().__init__(
            f"Invalid state transition from {from_state} to {to_state}"
            + (f" for load {load_id}" if load_id else ""),
            code="INVALID_STATE_TRANSITION",
        )
        self.from_state = from_state
        self.to_state = to_state
        self.load_id = load_id


class InvalidEventError(FreightHeroError):
    """Raised when an event is invalid for the current load state."""

    def __init__(self, event_type: str, load_state: str, reason: str = ""):
        super().__init__(
            f"Event {event_type} invalid for load state {load_state}: {reason}",
            code="INVALID_EVENT",
        )
        self.event_type = event_type
        self.load_state = load_state


class CustomerConfigNotFoundError(FreightHeroError):
    """Raised when customer configuration is not found."""

    def __init__(self, customer_id: str):
        super().__init__(
            f"Customer configuration not found: {customer_id}",
            code="CUSTOMER_CONFIG_NOT_FOUND",
        )
        self.customer_id = customer_id


class SOPBranchNotFoundError(FreightHeroError):
    """Raised when no SOP branch matches the event."""

    def __init__(self, event_type: str, load_state: str):
        super().__init__(
            f"No SOP branch found for event {event_type} in state {load_state}",
            code="SOP_BRANCH_NOT_FOUND",
        )
        self.event_type = event_type
        self.load_state = load_state


class MemoryOperationError(FreightHeroError):
    """Raised when a memory operation fails."""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            f"Memory operation {operation} failed: {reason}",
            code="MEMORY_OPERATION_ERROR",
        )
        self.operation = operation


class ToolExecutionError(FreightHeroError):
    """Raised when a tool execution fails."""

    def __init__(self, tool: str, reason: str):
        super().__init__(
            f"Tool {tool} execution failed: {reason}",
            code="TOOL_EXECUTION_ERROR",
        )
        self.tool = tool


class ConcurrencyError(FreightHeroError):
    """Raised when concurrent event processing conflicts."""

    def __init__(self, load_id: str, reason: str = ""):
        super().__init__(
            f"Concurrency conflict for load {load_id}: {reason}",
            code="CONCURRENCY_ERROR",
        )
        self.load_id = load_id


class ModelFallbackError(FreightHeroError):
    """Raised when all model providers fail."""

    def __init__(self, providers: list[str]):
        super().__init__(
            f"All model providers failed: {', '.join(providers)}",
            code="MODEL_FALLBACK_ERROR",
        )
        self.providers = providers