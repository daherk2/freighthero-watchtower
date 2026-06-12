"""Memory Manager service.

Manages the agent's memory operations including STM, LTM,
episodic, semantic, and procedural memory.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from src.domain.enums import MemoryOperation, MemoryScope, MemoryType
from src.domain.models import MemoryOperationLog
from src.application.ports import MemoryRepository, MemoryOperationLogRepository


class MemoryManager:
    """Application service for managing agent memory.

    Provides a unified interface for memory operations across
    STM (short-term), LTM (long-term), episodic, semantic,
    and procedural memory types.
    """

    def __init__(
        self,
        memory_repo: MemoryRepository,
        operation_log_repo: MemoryOperationLogRepository | None = None,
        stm_max_tokens: int = 4000,
        stm_max_events: int = 20,
    ):
        self._memory_repo = memory_repo
        self._operation_log_repo = operation_log_repo
        self._stm_max_tokens = stm_max_tokens
        self._stm_max_events = stm_max_events

    async def add_memory(
        self,
        memory_type: MemoryType,
        scope: MemoryScope,
        scope_id: str,
        content: str,
        tags: list[str] | None = None,
        source_event_ids: list[str] | None = None,
        confidence: float = 1.0,
        content_type: str = "fact",
        event_id: str | None = None,
        load_id: str | None = None,
    ) -> dict:
        """Add a new memory entry.

        Args:
            memory_type: Type of memory (episodic, semantic, procedural).
            scope: Scope of the memory (load, customer, global).
            scope_id: Identifier within the scope.
            content: The memory content.
            tags: Optional tags for categorization.
            source_event_ids: Event IDs that contributed to this memory.
            confidence: Confidence score (0-1).
            content_type: Type of content (fact, summary, procedure).
            event_id: Optional event ID for operation logging.
            load_id: Optional load ID for operation logging.

        Returns:
            Dictionary with memory_id and status.
        """
        memory_id = await self._memory_repo.add(
            memory_type=memory_type,
            scope=scope,
            scope_id=scope_id,
            content=content,
            tags=tags,
            source_event_ids=source_event_ids,
            confidence=confidence,
            content_type=content_type,
        )

        # Log the operation
        if self._operation_log_repo and event_id and load_id:
            await self._log_operation(
                operation=MemoryOperation.ADD,
                memory_type=memory_type,
                scope=scope,
                scope_id=scope_id,
                content=content,
                result={"memory_id": memory_id},
                event_id=event_id,
                load_id=load_id,
            )

        return {"memory_id": memory_id, "status": "added"}

    async def retrieve_memory(
        self,
        scope: MemoryScope,
        scope_id: str,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Retrieve memories matching the given criteria.

        Args:
            scope: Memory scope to search.
            scope_id: Identifier within the scope.
            memory_type: Optional filter by memory type.
            tags: Optional filter by tags.
            limit: Maximum number of results.

        Returns:
            List of memory dictionaries.
        """
        return await self._memory_repo.retrieve(
            scope=scope,
            scope_id=scope_id,
            memory_type=memory_type,
            tags=tags,
            limit=limit,
        )

    async def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        tags: list[str] | None = None,
        confidence: float | None = None,
    ) -> dict:
        """Update an existing memory entry.

        Args:
            memory_id: The memory identifier.
            content: New content (optional).
            tags: New tags (optional).
            confidence: New confidence score (optional).

        Returns:
            Dictionary with update status.
        """
        await self._memory_repo.update(
            memory_id=memory_id,
            content=content,
            tags=tags,
            confidence=confidence,
        )
        return {"memory_id": memory_id, "status": "updated"}

    async def delete_memory(self, memory_id: str) -> dict:
        """Delete a memory entry.

        Args:
            memory_id: The memory identifier.

        Returns:
            Dictionary with deletion status.
        """
        await self._memory_repo.delete(memory_id)
        return {"memory_id": memory_id, "status": "deleted"}

    async def summarize_memory(
        self,
        scope: MemoryScope,
        scope_id: str,
        memory_type: MemoryType,
    ) -> dict:
        """Summarize memories of a given type and scope.

        Args:
            scope: Memory scope.
            scope_id: Identifier within the scope.
            memory_type: Type of memories to summarize.

        Returns:
            Dictionary with summary_id and status.
        """
        summary_id = await self._memory_repo.summarize(
            scope=scope,
            scope_id=scope_id,
            memory_type=memory_type,
        )
        return {"summary_id": summary_id, "status": "summarized"}

    async def filter_memory(
        self,
        scope: MemoryScope,
        scope_id: str,
        memory_type: MemoryType,
        relevance_threshold: float = 0.5,
    ) -> dict:
        """Filter out low-relevance memories.

        Args:
            scope: Memory scope.
            scope_id: Identifier within the scope.
            memory_type: Type of memories to filter.
            relevance_threshold: Minimum relevance score to keep.

        Returns:
            Dictionary with count of removed memories.
        """
        removed = await self._memory_repo.filter(
            scope=scope,
            scope_id=scope_id,
            memory_type=memory_type,
            relevance_threshold=relevance_threshold,
        )
        return {"removed_count": removed, "status": "filtered"}

    async def get_stm_token_count(self, scope: MemoryScope, scope_id: str) -> int:
        """Get the approximate token count for short-term memory.

        Args:
            scope: Memory scope.
            scope_id: Identifier within the scope.

        Returns:
            Approximate token count.
        """
        return await self._memory_repo.get_stm_token_count(
            scope=scope, scope_id=scope_id
        )

    async def get_memory_metrics(self, scope: MemoryScope, scope_id: str) -> dict:
        """Get memory metrics for a given scope.

        Args:
            scope: Memory scope.
            scope_id: Identifier within the scope.

        Returns:
            Dictionary with memory metrics.
        """
        return await self._memory_repo.get_metrics(scope=scope, scope_id=scope_id)

    async def _log_operation(
        self,
        operation: MemoryOperation,
        memory_type: MemoryType,
        scope: MemoryScope,
        scope_id: str,
        content: str | None,
        result: dict,
        event_id: str,
        load_id: str,
    ) -> None:
        """Log a memory operation for audit and debugging."""
        if self._operation_log_repo is None:
            return

        log = MemoryOperationLog(
            operation_id=f"memop-{uuid.uuid4()}",
            event_id=event_id,
            load_id=load_id,
            operation=operation,
            memory_type=memory_type,
            scope=scope,
            scope_id=scope_id,
            content=content,
            result=result,
        )
        await self._operation_log_repo.save(log)