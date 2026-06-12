"""Load Service - Application service for load management.

Handles CRUD operations and state transitions for loads.
"""

import uuid
from datetime import datetime, timezone

from src.domain.enums import CustomerId, LoadState
from src.domain.exceptions import LoadNotFoundError, InvalidStateTransitionError
from src.domain.models import Load
from src.domain.value_objects import CustomerBehaviorConfig
from src.application.ports import LoadRepository, EventRepository
from src.application.dto import (
    CreateLoadRequest,
    CreateLoadResponse,
    ActiveLoadSummary,
    StateTransitionSummary,
)


class LoadService:
    """Application service for load management operations."""

    def __init__(self, load_repo: LoadRepository, event_repo: EventRepository | None = None):
        self._load_repo = load_repo
        self._event_repo = event_repo

    async def create_load(self, request: CreateLoadRequest) -> CreateLoadResponse:
        """Create a new load and optionally trigger the pipeline.

        Args:
            request: The create load request DTO.

        Returns:
            The create load response DTO with pipeline status.
        """
        load_id = request.load_id or f"load-{uuid.uuid4()}"
        load = Load(
            load_id=load_id,
            customer_id=CustomerId(request.customer_id),
            external_load_id=request.external_load_id,
            po_number=request.po_number,
            instructions=request.instructions,
            load_data=request.load_data,
            current_state=request.initial_state or LoadState.DISPATCHED,
            current_eta_utc=request.current_eta_utc,
        )

        saved_load = await self._load_repo.save(load)

        # Optionally trigger the pipeline
        pipeline_workflow = None
        pipeline_status = None
        if request.run_pipeline:
            try:
                result = await self._run_pipeline(saved_load)
                pipeline_workflow = result.get("workflow")
                pipeline_status = result.get("status")
            except Exception as e:
                pipeline_status = f"error: {e}"

        return CreateLoadResponse(
            load_id=saved_load.load_id,
            customer_id=saved_load.customer_id,
            external_load_id=saved_load.external_load_id,
            current_state=saved_load.current_state,
            created_at=saved_load.created_at or datetime.now(timezone.utc).isoformat(),
            pipeline_triggered=request.run_pipeline,
            pipeline_workflow=pipeline_workflow,
            pipeline_status=pipeline_status,
        )

    async def _run_pipeline(self, load: Load) -> dict:
        """Run the appropriate pipeline workflow for a load.

        Args:
            load: The load to process.

        Returns:
            Pipeline execution result.
        """
        from src.agent.llm import get_llm
        from src.agent.orchestrator import AgentOrchestrator
        from src.infrastructure.repositories import (
            get_agent_run_repository,
            get_memory_repository,
        )

        # Determine workflow based on load state
        if load.current_state in {LoadState.AT_DELIVERY, LoadState.CONFIRM_DELIVERY}:
            workflow = "confirm_delivery"
        else:
            workflow = "delivery_eta_checkpoint"

        # Create a synthetic event for the pipeline trigger
        from src.domain.models import Event
        from src.domain.enums import EventType
        event = Event(
            event_id=f"evt-{uuid.uuid4()}",
            event_type=EventType.LOAD_UPDATE,
            load_id=load.load_id,
            customer_id=load.customer_id,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            event_data={"trigger": "load_created", "initial_state": load.current_state},
        )
        if self._event_repo:
            await self._event_repo.save(event)

        # Run orchestrator
        llm = get_llm()
        orchestrator = AgentOrchestrator(
            load_repo=self._load_repo,
            event_repo=self._event_repo,
            agent_run_repo=get_agent_run_repository(self._load_repo._session) if hasattr(self._load_repo, '_session') else None,
            llm=llm,
        )

        result = await orchestrator.run(
            event_id=event.event_id,
            load_id=load.load_id,
            workflow=workflow,
        )

        return {
            "workflow": workflow,
            "status": result.get("status", "completed"),
            "run_id": result.get("run_id"),
        }

    async def get_load(self, load_id: str) -> dict:
        """Get a load by ID.

        Args:
            load_id: The load identifier.

        Returns:
            Load data dictionary.
        """
        load = await self._load_repo.get_by_id(load_id)
        return self._load_to_dict(load)

    async def get_active_loads(self) -> list[ActiveLoadSummary]:
        """Get all active loads.

        Returns:
            List of active load summaries.
        """
        loads = await self._load_repo.get_active_loads()
        return [
            ActiveLoadSummary(
                load_id=l.load_id,
                customer_id=l.customer_id,
                external_load_id=l.external_load_id,
                po_number=l.po_number,
                current_state=l.current_state,
                current_eta_utc=l.current_eta_utc,
                load_data=l.load_data or {},
                created_at=l.created_at,
                updated_at=l.updated_at,
            )
            for l in loads
        ]

    async def transition_state(self, load_id: str, new_state: LoadState) -> StateTransitionSummary:
        """Transition a load to a new state.

        Args:
            load_id: The load identifier.
            new_state: The target state.

        Returns:
            State transition summary.

        Raises:
            LoadNotFoundError: If the load doesn't exist.
            InvalidStateTransitionError: If the transition is invalid.
        """
        load = await self._load_repo.get_by_id(load_id)
        old_state = load.current_state
        load.transition_to(new_state)
        await self._load_repo.save(load)

        return StateTransitionSummary(
            load_id=load_id,
            from_state=old_state,
            to_state=new_state,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _load_to_dict(self, load: Load) -> dict:
        """Convert a Load domain model to a dictionary."""
        return {
            "load_id": load.load_id,
            "customer_id": load.customer_id if isinstance(load.customer_id, str) else load.customer_id.value,
            "external_load_id": load.external_load_id,
            "po_number": load.po_number,
            "instructions": load.instructions,
            "load_data": load.load_data,
            "current_state": load.current_state if isinstance(load.current_state, str) else load.current_state.value,
            "current_eta_utc": load.current_eta_utc,
            "created_at": load.created_at,
            "updated_at": load.updated_at,
        }