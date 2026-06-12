"""Event processing routes.

Handles inbound communications, tracking events, load updates,
and task submissions.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import CustomerId, EventType, LoadState
from src.domain.models import Event
from src.domain.exceptions import LoadNotFoundError, InvalidEventError
from src.infrastructure.database import DatabaseManager
from src.infrastructure.repositories import (
    get_load_repository,
    get_event_repository,
    get_agent_run_repository,
)
from src.application.dto import (
    InboundCommunicationRequest,
    TrackingEventRequest,
    LoadUpdateEventRequest,
    SubmitTaskRequest,
    SubmitTaskResponse,
    EventResponse,
)
from src.application.services.event_processor import EventProcessor
from src.agent.orchestrator import AgentOrchestrator
from src.agent.llm import get_llm

def _create_orchestrator(session):
    """Create an AgentOrchestrator with the necessary repositories."""
    from src.infrastructure.repositories import (
        get_load_repository,
        get_event_repository,
        get_agent_run_repository,
    )
    llm = get_llm()
    return AgentOrchestrator(
        load_repo=get_load_repository(session),
        event_repo=get_event_repository(session),
        agent_run_repo=get_agent_run_repository(session),
        memory_repo=None,  # Memory repo has interface mismatch, skip for now
        llm=llm,
    )


router = APIRouter()


async def get_db_session():
    """Dependency to get a database session."""
    from src.interfaces.app import app
    try:
        db_manager = app.state.db_manager
    except AttributeError:
        db_manager = None
    if db_manager is None:
        yield None
        return
    async with db_manager.async_session() as session:
        yield session


@router.post("/inbound-communication", response_model=EventResponse)
async def submit_inbound_communication(
    request: InboundCommunicationRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
):
    """Submit an inbound communication event."""
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured",
        )

    try:
        event_id = request.event_id

        # Create event with event_data dict
        event = Event(
            event_id=event_id,
            event_type=EventType.INBOUND_COMMUNICATION,
            load_id=request.load_id,
            customer_id=CustomerId(request.customer_id),
            occurred_at=request.occurred_at,
            event_data=request.inbound_communication,
        )

        load_repo = get_load_repository(session)
        event_repo = get_event_repository(session)
        await event_repo.save(event)

        # Process the event
        processor = EventProcessor(load_repo=load_repo, event_repo=event_repo, agent_run_repo=get_agent_run_repository(session), orchestrator=_create_orchestrator(session))
        result = await processor.process(event_id=event_id, load_id=request.load_id)

        await session.commit()

        return EventResponse(
            event_id=event_id,
            load_id=request.load_id,
            event_type=EventType.INBOUND_COMMUNICATION,
            status="processed",
            workflow=result["workflow"],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except LoadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load {request.load_id} not found",
        )
    except InvalidEventError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
@router.post("/tracking", response_model=EventResponse)
async def submit_tracking_event(
    request: TrackingEventRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
):
    """Submit a tracking ping event."""
    try:
        event_id = request.event_id

        event = Event(
            event_id=event_id,
            event_type=EventType.TRACKING,
            load_id=request.load_id,
            customer_id=CustomerId(request.customer_id),
            occurred_at=request.occurred_at,
            event_data=request.tracking,
        )

        load_repo = get_load_repository(session)
        event_repo = get_event_repository(session)
        await event_repo.save(event)

        processor = EventProcessor(load_repo=load_repo, event_repo=event_repo, agent_run_repo=get_agent_run_repository(session), orchestrator=_create_orchestrator(session))
        result = await processor.process(event_id=event_id, load_id=request.load_id)

        await session.commit()

        return EventResponse(
            event_id=event_id,
            load_id=request.load_id,
            event_type=EventType.TRACKING,
            status="processed",
            workflow=result["workflow"],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except LoadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load {request.load_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
@router.post("/load-update", response_model=EventResponse)
async def submit_load_update(
    request: LoadUpdateEventRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
):
    """Submit a load update event."""
    try:
        event_id = request.event_id

        event = Event(
            event_id=event_id,
            event_type=EventType.LOAD_UPDATE,
            load_id=request.load_id,
            customer_id=CustomerId(request.customer_id),
            occurred_at=request.occurred_at,
            event_data=request.load_update,
        )

        load_repo = get_load_repository(session)
        event_repo = get_event_repository(session)
        await event_repo.save(event)

        processor = EventProcessor(load_repo=load_repo, event_repo=event_repo, agent_run_repo=get_agent_run_repository(session), orchestrator=_create_orchestrator(session))
        result = await processor.process(event_id=event_id, load_id=request.load_id)

        await session.commit()

        return EventResponse(
            event_id=event_id,
            load_id=request.load_id,
            event_type=EventType.LOAD_UPDATE,
            status="processed",
            workflow=result["workflow"],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except LoadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load {request.load_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
@router.post("/submit-task", response_model=SubmitTaskResponse)
async def submit_task(
    request: SubmitTaskRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
):
    """Submit a task for agent processing.

    This is the main entry point for the AI challenge evaluation.
    """
    try:
        event_id = request.event_id or f"evt-{uuid.uuid4()}"
        load_id = request.load_id

        # Determine event type from task data
        event_data = request.event_data or {}

        from src.domain.models import Event
        event = Event(
            event_id=event_id,
            event_type=EventType(request.event_type) if request.event_type else EventType.INBOUND_COMMUNICATION,
            load_id=load_id,
            customer_id=CustomerId(request.customer_id),
            occurred_at=datetime.now(timezone.utc).isoformat(),
            event_data=event_data,
        )

        load_repo = get_load_repository(session)
        event_repo = get_event_repository(session)
        await event_repo.save(event)

        processor = EventProcessor(load_repo=load_repo, event_repo=event_repo, agent_run_repo=get_agent_run_repository(session), orchestrator=_create_orchestrator(session))
        result = await processor.process(event_id=event_id, load_id=load_id)

        await session.commit()

        return SubmitTaskResponse(
            event_id=event_id,
            load_id=load_id,
            status="processed",
            workflow=result["workflow"],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except (LoadNotFoundError, InvalidEventError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )