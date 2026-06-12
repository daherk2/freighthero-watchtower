"""Load management routes."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import CustomerId, LoadState
from src.domain.exceptions import LoadNotFoundError, InvalidStateTransitionError
from src.infrastructure.database import DatabaseManager
from src.infrastructure.repositories import (
    get_load_repository,
    get_event_repository,
)
from src.application.dto import (
    CreateLoadRequest,
    CreateLoadResponse,
    ActiveLoadSummary,
    StateTransitionSummary,
)
from src.application.services.load_service import LoadService

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
        await session.commit()


async def get_load_service(session: AsyncSession = Depends(get_db_session)) -> LoadService:
    """Dependency to get a LoadService instance."""
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured",
        )
    load_repo = get_load_repository(session)
    event_repo = get_event_repository(session)
    return LoadService(load_repo=load_repo, event_repo=event_repo)


@router.post("/", response_model=CreateLoadResponse, status_code=status.HTTP_201_CREATED)
async def create_load(
    request: CreateLoadRequest,
    service: LoadService = Depends(get_load_service),
):
    """Create a new load."""
    try:
        result = await service.create_load(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{load_id}")
async def get_load(
    load_id: str,
    service: LoadService = Depends(get_load_service),
):
    """Get a load by ID."""
    try:
        return await service.get_load(load_id)
    except LoadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load {load_id} not found",
        )


@router.get("/", response_model=list[ActiveLoadSummary])
async def get_active_loads(
    service: LoadService = Depends(get_load_service),
):
    """Get all active loads."""
    return await service.get_active_loads()


@router.post("/{load_id}/transition", response_model=StateTransitionSummary)
async def transition_load_state(
    load_id: str,
    new_state: LoadState,
    service: LoadService = Depends(get_load_service),
):
    """Transition a load to a new state."""
    try:
        return await service.transition_state(load_id, new_state)
    except LoadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load {load_id} not found",
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )