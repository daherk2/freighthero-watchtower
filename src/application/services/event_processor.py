"""Event Processor service.

Processes incoming events, validates them, and routes them to the
appropriate handler or agent workflow.
"""

import uuid
import logging
logger = logging.getLogger(__name__)
from datetime import datetime, timezone

from src.domain.enums import CustomerId, EventType, LoadState, SOPBranch
from src.domain.exceptions import InvalidEventError, LoadNotFoundError
from src.domain.models import Event, InboundCommunicationEvent, TrackingEvent, LoadUpdateEvent, TimerCallbackEvent, AgentRun
from src.application.ports import (
    EventQueue,
    EventRepository,
    LoadRepository,
    AgentRunRepository,
    ToolCallRepository,
)


class EventProcessor:
    """Processes incoming events and routes them to the appropriate handler.

    The EventProcessor is responsible for:
    1. Validating incoming events against the current load state
    2. Determining which workflow should handle the event
    3. Enqueuing events for agent processing
    4. Handling timer callbacks
    """

    def __init__(
        self,
        load_repo: LoadRepository,
        event_repo: EventRepository,
        event_queue: EventQueue | None = None,
        agent_run_repo: AgentRunRepository | None = None,
        orchestrator=None,
    ):
        self._load_repo = load_repo
        self._event_repo = event_repo
        self._event_queue = event_queue
        self._agent_run_repo = agent_run_repo
        self._orchestrator = orchestrator

    async def process(self, event_id: str, load_id: str) -> dict:
        """Process an event for a given load.

        Args:
            event_id: The event identifier.
            load_id: The load identifier.

        Returns:
            Processing result with routing information.
        """
        # 1. Load the event
        event = await self._event_repo.get_by_id(event_id)

        # 2. Load the current load state
        load = await self._load_repo.get_by_id(load_id)

        # 3. Validate event against current state
        self._validate_event(event, load)

        # 4. Determine the workflow
        workflow = self._determine_workflow(event, load)

        # 5. Mark event as processed
        await self._event_repo.mark_processed(event_id)

        # 6. Enqueue for agent processing
        if self._event_queue:
            await self._event_queue.enqueue(event)

        # 7. Run the agent orchestrator to get real tool_calls and memory_operations
        if self._orchestrator:
            try:
                logger.info(f"Starting orchestrator.run() for event {event_id}, load {load_id}, workflow {workflow}")
                result = await self._orchestrator.run(
                    event_id=event_id,
                    load_id=load_id,
                    workflow=workflow,
                )
                logger.info(f"Orchestrator completed for event {event_id}: run_id={result.get('run_id')}, "
                             f"tool_calls={len(result.get('tool_calls', []))}, "
                             f"memory_ops={len(result.get('memory_operations', []))}")
                return {
                    "event_id": event_id,
                    "load_id": load_id,
                    "workflow": workflow,
                    "status": "completed",
                    "run_id": result.get("run_id"),
                    "tool_calls": result.get("tool_calls", []),
                    "memory_operations": result.get("memory_operations", []),
                }
            except Exception as e:
                logger.error(f"Orchestrator failed for event {event_id}: {e}", exc_info=True)
                # Fall through to create a minimal record

        # Fallback: create a minimal agent run record if orchestrator is not available
        if self._agent_run_repo:
            agent_run = AgentRun(
                run_id=str(uuid.uuid4()),
                event_id=event_id,
                load_id=load_id,
                customer_id=load.customer_id if hasattr(load, 'customer_id') else CustomerId.CUSTOMER_A,
                workflow=workflow,
                sop_branch=SOPBranch.DRIVER_PROVIDES_ETA if load.current_state in {LoadState.DISPATCHED, LoadState.ON_ROUTE_TO_DELIVERY} else SOPBranch.ARRIVAL_CONFIRMATION,
                customer_rules_applied=[],
                tool_calls=[],
                memory_operations=[],
                state_before=load.current_state,
                state_after=load.current_state,
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            await self._agent_run_repo.save(agent_run)

        return {
            "event_id": event_id,
            "load_id": load_id,
            "workflow": workflow,
            "status": "routed",
        }

    async def process_timer_callback(self, timer_id: str, load_id: str) -> dict:
        """Process a timer callback event.

        Args:
            timer_id: The timer identifier.
            load_id: The load identifier.

        Returns:
            Processing result.
        """
        load = await self._load_repo.get_by_id(load_id)

        # Create a synthetic timer callback event
        event = TimerCallbackEvent(
            event_id=f"timer-{uuid.uuid4()}",
            load_id=load_id,
            customer_id=load.customer_id,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            timer_id=timer_id,
            timer_type="eta_followup",
            reason="eta_followup_timer_expired",
        )

        await self._event_repo.save(event)

        workflow = self._determine_workflow(event, load)

        return {
            "event_id": event.event_id,
            "load_id": load_id,
            "workflow": workflow,
            "status": "timer_routed",
        }

    def _validate_event(self, event: Event, load) -> None:
        """Validate that an event is processable for the given load state.

        Args:
            event: The event to validate.
            load: The current load state.

        Raises:
            InvalidEventError: If the event is invalid for the current state.
        """
        # Validate load is in an active state
        active_states = {
            LoadState.DISPATCHED,
            LoadState.ON_ROUTE_TO_DELIVERY,
            LoadState.AT_DELIVERY,
            LoadState.CONFIRM_DELIVERY,
        }
        if load.current_state not in active_states:
            raise InvalidEventError(
                event_type=str(event.event_type),
                load_state=str(load.current_state),
                reason=f"Cannot process event for load {load.load_id} in state {load.current_state}",
            )

        # Validate event belongs to the correct load
        if event.load_id != load.load_id:
            raise InvalidEventError(
                event_type=str(event.event_type),
                load_state=str(load.current_state),
                reason=f"Event {event.event_id} belongs to load {event.load_id}, not {load.load_id}",
            )

    def _determine_workflow(self, event: Event, load) -> str:
        """Determine which agent workflow should handle the event.

        Args:
            event: The event to route.
            load: The current load state.

        Returns:
            The workflow name.
        """
        # Route based on current load state
        if load.current_state in {LoadState.DISPATCHED, LoadState.ON_ROUTE_TO_DELIVERY}:
            return "delivery_eta_checkpoint"

        if load.current_state in {LoadState.AT_DELIVERY, LoadState.CONFIRM_DELIVERY}:
            return "confirm_delivery"

        # Route based on event type if state is ambiguous
        if isinstance(event, TrackingEvent):
            return "delivery_eta_checkpoint"

        if isinstance(event, InboundCommunicationEvent):
            # Could be either workflow depending on load state
            if load.current_state == LoadState.CONFIRM_DELIVERY:
                return "confirm_delivery"
            return "delivery_eta_checkpoint"

        if isinstance(event, LoadUpdateEvent):
            return "delivery_eta_checkpoint"

        if isinstance(event, TimerCallbackEvent):
            # Timer callbacks follow the current load state workflow
            if load.current_state == LoadState.CONFIRM_DELIVERY:
                return "confirm_delivery"
            return "delivery_eta_checkpoint"

        # Default to ETA checkpoint
        return "delivery_eta_checkpoint"