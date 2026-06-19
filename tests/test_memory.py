"""Tests for the memory system."""

import uuid
from datetime import datetime, timezone

import pytest

from src.domain.enums import MemoryOperation, MemoryScope, MemoryType
from src.application.services.memory_manager import MemoryManager


class MockMemoryRepository:
    """Mock memory repository for testing."""

    def __init__(self):
        self._memories = {}
        self._id_counter = 0

    async def add(self, memory_type, scope, scope_id, content, tags=None, source_event_ids=None, confidence=1.0, content_type="fact", expires_at=None):
        self._id_counter += 1
        memory_id = f"mem-{self._id_counter}"
        self._memories[memory_id] = {
            "id": memory_id,
            "memory_type": memory_type,
            "scope": scope,
            "scope_id": scope_id,
            "content": content,
            "tags": tags or [],
            "source_event_ids": source_event_ids or [],
            "confidence": confidence,
            "content_type": content_type,
            "relevance_score": 1.0,
            "access_count": 0,
        }
        return memory_id

    async def retrieve(self, scope, scope_id, memory_type=None, tags=None, limit=10):
        results = []
        for m in self._memories.values():
            if m["scope"] == scope and m["scope_id"] == scope_id:
                if memory_type and m["memory_type"] != memory_type:
                    continue
                if tags and not all(t in m["tags"] for t in tags):
                    continue
                results.append(m)
        return results[:limit]

    async def update(self, memory_id, content=None, tags=None, confidence=None):
        if memory_id in self._memories:
            if content is not None:
                self._memories[memory_id]["content"] = content
            if tags is not None:
                self._memories[memory_id]["tags"] = tags
            if confidence is not None:
                self._memories[memory_id]["confidence"] = confidence
            self._memories[memory_id]["access_count"] += 1

    async def delete(self, memory_id):
        if memory_id in self._memories:
            del self._memories[memory_id]

    async def summarize(self, scope, scope_id, memory_type):
        memories = [m for m in self._memories.values()
                     if m["scope"] == scope and m["scope_id"] == scope_id and m["memory_type"] == memory_type]
        if not memories:
            return ""
        summary_id = f"summary-{uuid.uuid4()}"
        return summary_id

    async def filter(self, scope, scope_id, memory_type, relevance_threshold=0.5):
        to_remove = [m_id for m_id, m in self._memories.items()
                     if m["scope"] == scope and m["scope_id"] == scope_id
                     and m["memory_type"] == memory_type and m["relevance_score"] < relevance_threshold]
        for m_id in to_remove:
            del self._memories[m_id]
        return len(to_remove)

    async def get_stm_token_count(self, scope, scope_id):
        memories = [m for m in self._memories.values()
                     if m["scope"] == scope and m["scope_id"] == scope_id
                     and m["memory_type"] == MemoryType.EPISODIC]
        return sum(len(m["content"]) // 4 for m in memories)

    async def get_metrics(self, scope, scope_id):
        memories = [m for m in self._memories.values()
                     if m["scope"] == scope and m["scope_id"] == scope_id]
        by_type = {}
        for m in memories:
            key = m["memory_type"] if isinstance(m["memory_type"], str) else m["memory_type"].value
            by_type[key] = by_type.get(key, 0) + 1
        return {
            "total_memories": len(memories),
            "by_type": by_type,
            "avg_confidence": sum(m["confidence"] for m in memories) / len(memories) if memories else 0,
            "avg_relevance": sum(m["relevance_score"] for m in memories) / len(memories) if memories else 0,
            "total_access_count": sum(m["access_count"] for m in memories),
        }

    async def run_maintenance(self):
        pass


class MockMemoryOperationLogRepository:
    """Mock memory operation log repository for testing."""

    def __init__(self):
        self._logs = []

    async def save(self, log):
        self._logs.append(log)
        return log

    async def get_by_load_id(self, load_id):
        return [l for l in self._logs if l.load_id == load_id]


class TestMemoryManager:
    """Tests for the MemoryManager service."""

    def setup_method(self):
        self.memory_repo = MockMemoryRepository()
        self.log_repo = MockMemoryOperationLogRepository()
        self.manager = MemoryManager(
            memory_repo=self.memory_repo,
            operation_log_repo=self.log_repo,
        )

    @pytest.mark.asyncio
    async def test_add_memory(self):
        """Test adding a memory entry."""
        result = await self.manager.add_memory(
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Driver arrived at delivery",
            tags=["arrival", "delivery"],
        )
        assert result["status"] == "added"
        assert result["memory_id"] is not None

    @pytest.mark.asyncio
    async def test_retrieve_memory(self):
        """Test retrieving memories."""
        # Add some memories first
        await self.manager.add_memory(
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Driver arrived",
        )
        await self.manager.add_memory(
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Customer requires manual POD validation",
        )

        # Retrieve all memories for this load
        results = await self.manager.retrieve_memory(
            scope=MemoryScope.LOAD,
            scope_id="load-001",
        )
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_retrieve_memory_by_type(self):
        """Test retrieving memories filtered by type."""
        await self.manager.add_memory(
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Driver arrived",
        )
        await self.manager.add_memory(
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Customer config",
        )

        results = await self.manager.retrieve_memory(
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            memory_type=MemoryType.EPISODIC,
        )
        assert len(results) == 1
        assert results[0]["memory_type"] == MemoryType.EPISODIC

    @pytest.mark.asyncio
    async def test_update_memory(self):
        """Test updating a memory entry."""
        result = await self.manager.add_memory(
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Original content",
        )
        memory_id = result["memory_id"]

        update_result = await self.manager.update_memory(
            memory_id=memory_id,
            content="Updated content",
        )
        assert update_result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_delete_memory(self):
        """Test deleting a memory entry."""
        result = await self.manager.add_memory(
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="To be deleted",
        )
        memory_id = result["memory_id"]

        delete_result = await self.manager.delete_memory(memory_id)
        assert delete_result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_summarize_memory(self):
        """Test summarizing memories."""
        # Add multiple episodic memories
        for i in range(5):
            await self.manager.add_memory(
                memory_type=MemoryType.EPISODIC,
                scope=MemoryScope.LOAD,
                scope_id="load-001",
                content=f"Event {i}: Driver update",
            )

        result = await self.manager.summarize_memory(
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            memory_type=MemoryType.EPISODIC,
        )
        assert result["status"] == "summarized"
        assert result["summary_id"] is not None

    @pytest.mark.asyncio
    async def test_filter_memory(self):
        """Test filtering low-relevance memories."""
        result = await self.manager.filter_memory(
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            memory_type=MemoryType.EPISODIC,
            relevance_threshold=0.5,
        )
        assert result["status"] == "filtered"

    @pytest.mark.asyncio
    async def test_get_stm_token_count(self):
        """Test getting STM token count."""
        await self.manager.add_memory(
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Short memory",
        )

        token_count = await self.manager.get_stm_token_count(
            scope=MemoryScope.LOAD,
            scope_id="load-001",
        )
        assert token_count > 0

    @pytest.mark.asyncio
    async def test_get_memory_metrics(self):
        """Test getting memory metrics."""
        await self.manager.add_memory(
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Episodic memory",
        )
        await self.manager.add_memory(
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Semantic memory",
        )

        metrics = await self.manager.get_memory_metrics(
            scope=MemoryScope.LOAD,
            scope_id="load-001",
        )
        assert metrics["total_memories"] == 2
        assert "episodic" in metrics["by_type"]
        assert "semantic" in metrics["by_type"]

    @pytest.mark.asyncio
    async def test_memory_with_operation_logging(self):
        """Test that memory operations are logged."""
        result = await self.manager.add_memory(
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.LOAD,
            scope_id="load-001",
            content="Logged memory",
            event_id="evt-001",
            load_id="load-001",
        )
        assert result["status"] == "added"
        assert len(self.log_repo._logs) == 1