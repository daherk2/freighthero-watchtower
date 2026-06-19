"""Tests for observability module."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestSetupLogging:
    """Tests for logging setup."""

    def test_setup_logging_default_level(self):
        """Test setup_logging with default level."""
        from src.infrastructure.observability import setup_logging
        # Should not raise
        setup_logging("INFO")

    def test_setup_logging_debug_level(self):
        """Test setup_logging with DEBUG level."""
        from src.infrastructure.observability import setup_logging
        setup_logging("DEBUG")

    def test_setup_logging_warning_level(self):
        """Test setup_logging with WARNING level."""
        from src.infrastructure.observability import setup_logging
        setup_logging("WARNING")


class TestSetupTracing:
    """Tests for tracing setup."""

    def test_setup_tracing_returns_tracer(self):
        """Test that setup_tracing returns a tracer."""
        from src.infrastructure.observability import setup_tracing
        tracer = setup_tracing()
        assert tracer is not None

    def test_get_tracer(self):
        """Test that get_tracer returns a tracer."""
        from src.infrastructure.observability import get_tracer
        tracer = get_tracer()
        assert tracer is not None


class TestSetupInstrumentation:
    """Tests for instrumentation setup."""

    def test_setup_instrumentation_with_app(self):
        """Test setup_instrumentation with a FastAPI app."""
        from src.infrastructure.observability import setup_instrumentation
        # Should not raise
        mock_app = MagicMock()
        setup_instrumentation(app=mock_app)

    def test_setup_instrumentation_without_app(self):
        """Test setup_instrumentation without an app."""
        from src.infrastructure.observability import setup_instrumentation
        # Should not raise
        setup_instrumentation()