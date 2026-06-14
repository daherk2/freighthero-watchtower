"""Celery task queue configuration and tasks."""

import logging

from celery import Celery

from src.infrastructure.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

celery_app = Celery(
    "freighthero",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "src.infrastructure.queue.tasks.process_event": {"queue": "events"},
        "src.infrastructure.queue.tasks.run_agent_workflow": {"queue": "agent"},
        "src.infrastructure.queue.tasks.fire_timer": {"queue": "timers"},
        "src.infrastructure.queue.tasks.memory_maintenance": {"queue": "memory"},
    },
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_event(self, event_id: str, load_id: str) -> None:
    """Process an incoming event through the event processor."""
    import asyncio
    from src.infrastructure.database import DatabaseManager
    from src.infrastructure.config import get_settings

    settings = get_settings()
    db = DatabaseManager(settings.database_url)

    async def _process():
        from src.application.services.event_processor import EventProcessor
        from src.infrastructure.repositories import get_load_repository, get_event_repository

        async with db.async_session() as session:
            load_repo = get_load_repository(session)
            event_repo = get_event_repository(session)
            processor = EventProcessor(load_repo=load_repo, event_repo=event_repo)
            await processor.process(event_id=event_id, load_id=load_id)

    try:
        asyncio.run(_process())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def run_agent_workflow(self, event_id: str, load_id: str, workflow: str) -> None:
    """Run an agent workflow for an event."""
    import asyncio
    from src.infrastructure.database import DatabaseManager
    from src.infrastructure.config import get_settings

    settings = get_settings()
    db = DatabaseManager(settings.database_url)

    async def _run():
        from src.agent.orchestrator import AgentOrchestrator
        from src.infrastructure.repositories import get_load_repository, get_event_repository, get_agent_run_repository

        async with db.async_session() as session:
            load_repo = get_load_repository(session)
            event_repo = get_event_repository(session)
            run_repo = get_agent_run_repository(session)
            orchestrator = AgentOrchestrator(
                load_repo=load_repo,
                event_repo=event_repo,
                run_repo=run_repo,
            )
            await orchestrator.run(event_id=event_id, load_id=load_id, workflow=workflow)

    try:
        asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2)
def fire_timer(self, timer_id: str, load_id: str) -> None:
    """Fire a scheduled timer callback."""
    import asyncio
    from src.infrastructure.database import DatabaseManager
    from src.infrastructure.config import get_settings

    settings = get_settings()
    db = DatabaseManager(settings.database_url)

    async def _fire():
        from src.application.services.event_processor import EventProcessor
        from src.infrastructure.repositories import get_load_repository, get_event_repository

        async with db.async_session() as session:
            load_repo = get_load_repository(session)
            event_repo = get_event_repository(session)
            processor = EventProcessor(load_repo=load_repo, event_repo=event_repo)
            await processor.process_timer_callback(timer_id=timer_id, load_id=load_id)

    try:
        asyncio.run(_fire())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def memory_maintenance() -> None:
    """Run periodic memory maintenance tasks (summarization, pruning, etc.)."""
    import asyncio
    from src.infrastructure.database import DatabaseManager
    from src.infrastructure.config import get_settings

    settings = get_settings()
    db = DatabaseManager(settings.database_url)

    async def _maintain():
        from src.infrastructure.repositories import get_memory_repository

        async with db.async_session() as session:
            memory_repo = get_memory_repository(session)
            await memory_repo.run_maintenance()

    try:
        asyncio.run(_maintain())
    except Exception:
        logger.exception("Memory maintenance task failed")