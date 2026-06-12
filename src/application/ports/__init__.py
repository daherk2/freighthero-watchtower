"""Application ports (interfaces) for FreightHero Watchtower.

These define the contracts that infrastructure must implement.
Business logic depends on these abstractions, not concrete implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.enums import (
    CustomerId,
    LoadState,
    MemoryOperation,
    MemoryScope,
    MemoryType,
)
from src.domain.models import (
    AgentRun,
    Event,
    Load,
    MemoryOperationLog,
    ToolCall,
)
from src.domain.value_objects import CustomerBehaviorConfig


class LoadRepository(ABC):
    """Port for load persistence."""

    @abstractmethod
    async def get_by_id(self, load_id: str) -> Load | None:
        """Get a load by ID."""

    @abstractmethod
    async def save(self, load: Load) -> Load:
        """Save a load (create or update)."""

    @abstractmethod
    async def update_state(self, load_id: str, new_state: LoadState, reason: str) -> Load:
        """Update a load's milestone state."""

    @abstractmethod
    async def update_eta(self, load_id: str, eta_utc: str, source: str) -> Load:
        """Update a load's ETA."""


class EventRepository(ABC):
    """Port for event persistence."""

    @abstractmethod
    async def save(self, event: Event) -> Event:
        """Save an event."""

    @abstractmethod
    async def get_by_id(self, event_id: str) -> Event | None:
        """Get an event by ID."""

    @abstractmethod
    async def get_by_load_id(self, load_id: str, limit: int = 50) -> list[Event]:
        """Get events for a load, ordered by occurrence."""


class ToolCallRepository(ABC):
    """Port for tool call persistence."""

    @abstractmethod
    async def save(self, tool_call: ToolCall) -> ToolCall:
        """Save a tool call record."""

    @abstractmethod
    async def get_by_load_id(self, load_id: str) -> list[ToolCall]:
        """Get all tool calls for a load."""

    @abstractmethod
    async def get_by_event_id(self, event_id: str) -> list[ToolCall]:
        """Get all tool calls for an event."""


class AgentRunRepository(ABC):
    """Port for agent run persistence."""

    @abstractmethod
    async def save(self, run: AgentRun) -> AgentRun:
        """Save an agent run record."""

    @abstractmethod
    async def get_by_id(self, run_id: str) -> AgentRun | None:
        """Get an agent run by ID."""

    @abstractmethod
    async def get_by_load_id(self, load_id: str, limit: int = 20) -> list[AgentRun]:
        """Get agent runs for a load."""

    @abstractmethod
    async def get_active_runs(self, limit: int = 100) -> list[AgentRun]:
        """Get currently active (in-progress) agent runs."""


class MemoryRepository(ABC):
    """Port for memory persistence."""

    @abstractmethod
    async def add(
        self,
        memory_type: MemoryType,
        scope: MemoryScope,
        scope_id: str,
        content: str,
        content_type: str = "fact",
        tags: list[str] | None = None,
        confidence: float = 1.0,
        expires_at: datetime | None = None,
    ) -> dict:
        """Add a memory entry."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        memory_types: list[MemoryType] | None = None,
        scope: MemoryScope | None = None,
        scope_id: str | None = None,
        limit: int = 10,
        min_relevance: float = 0.5,
    ) -> dict:
        """Retrieve relevant memories."""

    @abstractmethod
    async def update(
        self,
        memory_id: str,
        content: str | None = None,
        confidence: float | None = None,
        relevance_score: float | None = None,
    ) -> dict:
        """Update an existing memory."""

    @abstractmethod
    async def delete(
        self,
        memory_id: str | None = None,
        memory_type: MemoryType | None = None,
        scope: MemoryScope | None = None,
        scope_id: str | None = None,
        reason: str = "",
    ) -> dict:
        """Delete memory entries."""

    @abstractmethod
    async def summarize(
        self,
        memory_type: MemoryType = MemoryType.STM,
        scope_id: str = "",
        strategy: str = "compress_older",
        max_tokens: int | None = None,
        preserve_recent_n: int = 5,
    ) -> dict:
        """Summarize memory context."""

    @abstractmethod
    async def filter_memories(
        self,
        memory_type: MemoryType = MemoryType.STM,
        scope_id: str = "",
        filter_criteria: str = "low_relevance",
        threshold: float | None = None,
    ) -> dict:
        """Filter and remove irrelevant memories."""

    @abstractmethod
    async def get_stm_token_count(self, load_id: str) -> int:
        """Get current STM token count for a load."""

    @abstractmethod
    async def get_metrics(self, load_id: str | None = None) -> dict:
        """Get memory metrics."""


class MemoryOperationLogRepository(ABC):
    """Port for memory operation log persistence."""

    @abstractmethod
    async def save(self, log: MemoryOperationLog) -> MemoryOperationLog:
        """Save a memory operation log."""

    @abstractmethod
    async def get_by_load_id(self, load_id: str) -> list[MemoryOperationLog]:
        """Get memory operations for a load."""


class EventQueue(ABC):
    """Port for event queue operations."""

    @abstractmethod
    async def enqueue(self, event: Event) -> str:
        """Enqueue an event for processing. Returns task ID."""

    @abstractmethod
    async def enqueue_timer_callback(
        self, load_id: str, timer_id: str, timer_type: str, fire_at_utc: str, reason: str
    ) -> str:
        """Enqueue a timer callback for future processing."""

    @abstractmethod
    async def cancel_timer(self, timer_id: str) -> bool:
        """Cancel a scheduled timer."""

    @abstractmethod
    async def cancel_timers_by_type(self, load_id: str, timer_type: str | None = None) -> int:
        """Cancel timers by type for a load. Returns count cancelled."""


class CustomerConfigResolver(ABC):
    """Port for resolving customer-specific behavior configuration."""

    @abstractmethod
    async def get_config(self, customer_id: CustomerId) -> CustomerBehaviorConfig:
        """Get behavior configuration for a customer."""

    @abstractmethod
    async def get_all_configs(self) -> dict[CustomerId, CustomerBehaviorConfig]:
        """Get all customer configurations."""


class SOPProvider(ABC):
    """Port for providing SOP content to the agent."""

    @abstractmethod
    async def get_sop(self, workflow: str, customer_id: CustomerId) -> str:
        """Get compiled SOP content for a workflow and customer."""

    @abstractmethod
    async def get_base_sop(self, workflow: str) -> str:
        """Get base SOP content for a workflow (without customer-specific modifications)."""


class LLMProvider(ABC):
    """Port for LLM inference with fallback support."""

    @abstractmethod
    async def invoke(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Invoke the LLM with messages and optional tools. Returns response dict."""

    @abstractmethod
    async def invoke_with_fallback(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        """Invoke the LLM with fallback to alternative providers."""