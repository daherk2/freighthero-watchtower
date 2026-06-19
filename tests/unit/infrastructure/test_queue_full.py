"""Tests for infrastructure queue module."""

import sys
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


class TestCeleryConfiguration:
    """Tests for Celery app configuration."""

    def test_celery_app_exists(self):
        """Test that the Celery app is configured."""
        from src.infrastructure.queue import celery_app
        assert celery_app is not None
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True

    def test_task_routes_configured(self):
        """Test that task routes are configured."""
        from src.infrastructure.queue import celery_app
        routes = celery_app.conf.task_routes
        assert "src.infrastructure.queue.tasks.process_event" in routes
        assert routes["src.infrastructure.queue.tasks.process_event"]["queue"] == "events"
        assert "src.infrastructure.queue.tasks.run_agent_workflow" in routes
        assert routes["src.infrastructure.queue.tasks.run_agent_workflow"]["queue"] == "agent"
        assert "src.infrastructure.queue.tasks.fire_timer" in routes
        assert routes["src.infrastructure.queue.tasks.fire_timer"]["queue"] == "timers"
        assert "src.infrastructure.queue.tasks.memory_maintenance" in routes
        assert routes["src.infrastructure.queue.tasks.memory_maintenance"]["queue"] == "memory"

    def test_celery_settings(self):
        """Test Celery app settings."""
        from src.infrastructure.queue import celery_app
        assert celery_app.conf.task_track_started is True
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.worker_prefetch_multiplier == 1

    def test_process_event_task_registered(self):
        """Test that process_event task is registered."""
        from src.infrastructure.queue import process_event
        assert process_event is not None
        assert process_event.name == "src.infrastructure.queue.process_event"
        assert process_event.max_retries == 3
        assert process_event.default_retry_delay == 5

    def test_run_agent_workflow_task_registered(self):
        """Test that run_agent_workflow task is registered."""
        from src.infrastructure.queue import run_agent_workflow
        assert run_agent_workflow is not None
        assert run_agent_workflow.max_retries == 2
        assert run_agent_workflow.default_retry_delay == 10

    def test_fire_timer_task_registered(self):
        """Test that fire_timer task is registered."""
        from src.infrastructure.queue import fire_timer
        assert fire_timer is not None
        assert fire_timer.max_retries == 2

    def test_memory_maintenance_task_registered(self):
        """Test that memory_maintenance task is registered."""
        from src.infrastructure.queue import memory_maintenance
        assert memory_maintenance is not None