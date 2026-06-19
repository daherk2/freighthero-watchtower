"""Tests for domain exceptions."""

import pytest

from src.domain.enums import CustomerId
from src.domain.exceptions import (
    FreightHeroError,
    LoadNotFoundError,
    InvalidStateTransitionError,
    InvalidEventError,
    CustomerConfigNotFoundError,
    SOPBranchNotFoundError,
    MemoryOperationError,
    ToolExecutionError,
    ConcurrencyError,
    ModelFallbackError,
)


class TestFreightHeroError:
    """Tests for base FreightHeroError."""

    def test_base_error(self):
        """Test base error creation."""
        error = FreightHeroError("test error")
        assert str(error) == "test error"
        assert isinstance(error, Exception)

    def test_base_error_with_code(self):
        """Test base error with code."""
        error = FreightHeroError("something failed", code="TEST_ERROR")
        assert error.message == "something failed"
        assert error.code == "TEST_ERROR"


class TestLoadNotFoundError:
    """Tests for LoadNotFoundError."""

    def test_load_not_found(self):
        """Test LoadNotFoundError creation."""
        error = LoadNotFoundError("load-123")
        assert "load-123" in str(error)
        assert isinstance(error, FreightHeroError)
        assert error.load_id == "load-123"


class TestInvalidStateTransitionError:
    """Tests for InvalidStateTransitionError."""

    def test_invalid_transition(self):
        """Test InvalidStateTransitionError creation."""
        error = InvalidStateTransitionError("dispatched", "pod_collected")
        assert "dispatched" in str(error)
        assert "pod_collected" in str(error)
        assert isinstance(error, FreightHeroError)

    def test_invalid_transition_with_load_id(self):
        """Test InvalidStateTransitionError with load_id."""
        error = InvalidStateTransitionError("dispatched", "pod_collected", load_id="load-1")
        assert "load-1" in str(error)


class TestInvalidEventError:
    """Tests for InvalidEventError."""

    def test_invalid_event(self):
        """Test InvalidEventError creation."""
        error = InvalidEventError("tracking", "dispatched", "not allowed")
        assert "tracking" in str(error)
        assert "dispatched" in str(error)
        assert isinstance(error, FreightHeroError)


class TestCustomerConfigNotFoundError:
    """Tests for CustomerConfigNotFoundError."""

    def test_customer_config_not_found(self):
        """Test CustomerConfigNotFoundError creation."""
        error = CustomerConfigNotFoundError("customer_a")
        assert "customer_a" in str(error)
        assert isinstance(error, FreightHeroError)


class TestSOPBranchNotFoundError:
    """Tests for SOPBranchNotFoundError."""

    def test_sop_branch_not_found(self):
        """Test SOPBranchNotFoundError creation."""
        error = SOPBranchNotFoundError("inbound_communication", "on_route")
        assert "inbound_communication" in str(error)
        assert "on_route" in str(error)
        assert isinstance(error, FreightHeroError)


class TestMemoryOperationError:
    """Tests for MemoryOperationError."""

    def test_memory_operation_error(self):
        """Test MemoryOperationError creation."""
        error = MemoryOperationError("add", "database error")
        assert "add" in str(error)
        assert "database error" in str(error)
        assert isinstance(error, FreightHeroError)


class TestToolExecutionError:
    """Tests for ToolExecutionError."""

    def test_tool_execution_error(self):
        """Test ToolExecutionError creation."""
        error = ToolExecutionError("send_sms", "timeout")
        assert "send_sms" in str(error)
        assert "timeout" in str(error)
        assert isinstance(error, FreightHeroError)


class TestConcurrencyError:
    """Tests for ConcurrencyError."""

    def test_concurrency_error(self):
        """Test ConcurrencyError creation."""
        error = ConcurrencyError("load-1", "simultaneous updates")
        assert "load-1" in str(error)
        assert isinstance(error, FreightHeroError)


class TestModelFallbackError:
    """Tests for ModelFallbackError."""

    def test_model_fallback_error(self):
        """Test ModelFallbackError creation."""
        error = ModelFallbackError(["openai", "anthropic"])
        assert "openai" in str(error)
        assert "anthropic" in str(error)
        assert isinstance(error, FreightHeroError)