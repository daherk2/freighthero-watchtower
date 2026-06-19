"""Tests for infrastructure queue tasks."""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock langchain_openai before any imports
sys.modules["langchain_openai"] = MagicMock()


class TestCeleryConfiguration:
    """Tests for Celery app configuration."""

    def test_celery_app_exists(self):
        """Test that the Celery app is configured."""
        from src.infrastructure.queue import celery_app
        assert celery_app is not None
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.timezone == "UTC"

    def test_task_routes_configured(self):
        """Test that task routes are configured."""
        from src.infrastructure.queue import celery_app
        routes = celery_app.conf.task_routes
        assert "src.infrastructure.queue.tasks.process_event" in routes
        assert "src.infrastructure.queue.tasks.run_agent_workflow" in routes
        assert "src.infrastructure.queue.tasks.fire_timer" in routes
        assert "src.infrastructure.queue.tasks.memory_maintenance" in routes

    def test_process_event_task_registered(self):
        """Test that process_event task is registered."""
        from src.infrastructure.queue import process_event
        assert process_event is not None
        assert process_event.name == "src.infrastructure.queue.process_event"

    def test_run_agent_workflow_task_registered(self):
        """Test that run_agent_workflow task is registered."""
        from src.infrastructure.queue import run_agent_workflow
        assert run_agent_workflow is not None

    def test_fire_timer_task_registered(self):
        """Test that fire_timer task is registered."""
        from src.infrastructure.queue import fire_timer
        assert fire_timer is not None

    def test_memory_maintenance_task_registered(self):
        """Test that memory_maintenance task is registered."""
        from src.infrastructure.queue import memory_maintenance
        assert memory_maintenance is not None


class TestProcessEventTask:
    """Tests for the process_event Celery task."""

    def test_process_event_retries_on_failure(self):
        """Test that process_event retries on exception."""
        from src.infrastructure.queue import process_event
        assert process_event.max_retries == 3

    def test_process_event_default_retry_delay(self):
        """Test that process_event has correct default retry delay."""
        from src.infrastructure.queue import process_event
        assert process_event.default_retry_delay == 5


class TestRunAgentWorkflowTask:
    """Tests for the run_agent_workflow Celery task."""

    def test_run_agent_workflow_retries(self):
        """Test that run_agent_workflow has correct retry config."""
        from src.infrastructure.queue import run_agent_workflow
        assert run_agent_workflow.max_retries == 2
        assert run_agent_workflow.default_retry_delay == 10


class TestFireTimerTask:
    """Tests for the fire_timer Celery task."""

    def test_fire_timer_retries(self):
        """Test that fire_timer has correct retry config."""
        from src.infrastructure.queue import fire_timer
        assert fire_timer.max_retries == 2