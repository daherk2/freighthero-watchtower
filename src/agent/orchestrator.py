"""Agent Orchestrator - Coordinates workflow execution.

The orchestrator is the main entry point for agent execution.
It selects the appropriate workflow, initializes context, and
manages the full execution lifecycle.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

from src.domain.enums import ConfirmDeliveryBranch, CustomerId, EventType, LoadState, SOPBranch
from src.domain.exceptions import LoadNotFoundError, InvalidEventError
from src.domain.models import AgentRun
from src.application.ports import (
    AgentRunRepository,
    EventRepository,
    LoadRepository,
    MemoryRepository,
    ToolCallRepository,
)
from src.application.services.customer_resolver import CustomerBehaviorResolver
from src.application.services.sop_compiler import SOPCompiler
from src.agent.eta_checkpoint import create_eta_checkpoint_workflow
from src.agent.confirm_delivery import create_confirm_delivery_workflow


def _resolve_sop_branch(branch_value: str) -> SOPBranch | ConfirmDeliveryBranch:
    """Resolve a SOP branch string to the appropriate enum member.
    
    Tries SOPBranch first (ETA Checkpoint branches), then falls back to
    ConfirmDeliveryBranch (Confirm Delivery branches).
    """
    try:
        return SOPBranch(branch_value)
    except ValueError:
        return ConfirmDeliveryBranch(branch_value)


class AgentOrchestrator:
    """Orchestrates agent workflow execution.

    The orchestrator:
    1. Loads the event and load context
    2. Resolves customer behavior configuration
    3. Compiles the SOP with customer-specific rules
    4. Selects and initializes the appropriate LangGraph workflow
    5. Executes the workflow and collects results
    6. Records tool calls and memory operations
    """

    def __init__(
        self,
        load_repo: LoadRepository,
        event_repo: EventRepository,
        agent_run_repo: AgentRunRepository,
        memory_repo: MemoryRepository | None = None,
        tool_call_repo: ToolCallRepository | None = None,
        customer_resolver: CustomerBehaviorResolver | None = None,
        sop_compiler: SOPCompiler | None = None,
        llm=None,
    ):
        self._load_repo = load_repo
        self._event_repo = event_repo
        self._agent_run_repo = agent_run_repo
        self._memory_repo = memory_repo
        self._tool_call_repo = tool_call_repo
        self._customer_resolver = customer_resolver or CustomerBehaviorResolver()
        self._sop_compiler = sop_compiler or SOPCompiler(self._customer_resolver)
        self._llm = llm

        # Pre-compile workflows
        self._workflows = {
            "delivery_eta_checkpoint": create_eta_checkpoint_workflow(llm=self._llm),
            "confirm_delivery": create_confirm_delivery_workflow(llm=self._llm),
        }

    async def run(
        self,
        event_id: str,
        load_id: str,
        workflow: str,
    ) -> dict:
        """Run an agent workflow for an event.

        Args:
            event_id: The event to process.
            load_id: The load context.
            workflow: The workflow to execute.

        Returns:
            Dictionary with workflow results.
        """
        # 1. Load context
        event = await self._event_repo.get_by_id(event_id)
        load = await self._load_repo.get_by_id(load_id)
        customer_id = CustomerId(load.customer_id) if isinstance(load.customer_id, str) else load.customer_id

        # 2. Resolve customer config
        customer_config = await self._customer_resolver.get_config(customer_id)
        customer_config_dict = {
            "customer_id": customer_config.customer_id,
            "escalation_channel": customer_config.escalation_channel,
            "missing_load_info_action": customer_config.missing_load_info_action,
            "pod_validation_type": customer_config.pod_validation_type,
            "pod_received_visibility": customer_config.pod_received_visibility,
            "delivered_without_pod_visibility": customer_config.delivered_without_pod_visibility,
            "delivery_geofence_radius_miles": customer_config.delivery_geofence_radius_miles,
            "eta_followup_timer_minutes": customer_config.eta_followup_timer_minutes,
            "lumper_receipt_handling": customer_config.lumper_receipt_handling,
            "first_arrival_message": customer_config.first_arrival_message,
        }

        # 3. Compile SOP
        sop_content = await self._sop_compiler.get_sop(workflow, customer_id)

        # 4. Initialize workflow state
        initial_state = {
            "event_id": event_id,
            "load_id": load_id,
            "customer_id": customer_id if isinstance(customer_id, str) else customer_id.value,
            "event_type": event.event_type if isinstance(event.event_type, str) else event.event_type.value,
            "event_data": event.event_data,
            "load_data": load.load_data,
            "current_state": load.current_state if isinstance(load.current_state, str) else load.current_state.value,
            "current_eta_utc": load.current_eta_utc,
            "customer_config": customer_config_dict,
            "sop_content": sop_content,
            "messages": [],
            "tool_calls": [],
            "memory_operations": [],
            "actions_taken": [],
            "followup_scheduled": False,
            "escalation_sent": False,
        }

        # 5. Execute workflow
        workflow_graph = self._workflows.get(workflow)
        if workflow_graph is None:
            raise ValueError(f"Unknown workflow: {workflow}")

        config = {"configurable": {"thread_id": f"{load_id}-{event_id}"}}
        result = await workflow_graph.ainvoke(initial_state, config)

        # 6. Process memory operations
        if self._memory_repo:
            for mem_op in result.get("memory_operations", []):
                try:
                    from src.domain.enums import MemoryOperation, MemoryScope, MemoryType
                    await self._memory_repo.add(
                        memory_type=MemoryType(mem_op.get("memory_type", "episodic")),
                        scope=MemoryScope(mem_op.get("scope", "load")),
                        scope_id=mem_op.get("scope_id", load_id),
                        content=mem_op.get("content", ""),
                        tags=mem_op.get("tags", []),
                    )
                except Exception:
                    logger.exception("Failed to persist memory operation")

        # 7. Save agent run record
        run_id = str(uuid.uuid4())
        state_after = result.get("state_after")
        if self._agent_run_repo:
            try:
                from src.domain.enums import SOPBranch
                # Convert workflow dicts to proper ToolCall and MemoryOperationLog objects
                from src.domain.models import ToolCall, MemoryOperationLog
                from src.domain.enums import MemoryOperation, MemoryType, MemoryScope
                
                raw_tool_calls = result.get("tool_calls", [])
                tool_calls = [
                    ToolCall(
                        event_id=event_id,
                        load_id=load_id,
                        tool=tc.get("tool", "unknown"),
                        arguments=tc.get("arguments", {}),
                        result=tc.get("result", {}),
                    )
                    for tc in raw_tool_calls
                ]
                
                raw_memory_ops = result.get("memory_operations", [])
                memory_operations = [
                    MemoryOperationLog(
                        event_id=event_id,
                        load_id=load_id,
                        operation=MemoryOperation(mo.get("operation", "add")),
                        memory_type=MemoryType(mo.get("memory_type", "episodic")),
                        scope=MemoryScope(mo.get("scope", "load")),
                        scope_id=mo.get("scope_id", load_id),
                        content=mo.get("content", ""),
                        result=mo.get("result", {}),
                    )
                    for mo in raw_memory_ops
                ]
                
                agent_run = AgentRun(
                    run_id=run_id,
                    event_id=event_id,
                    load_id=load_id,
                    customer_id=customer_id if isinstance(customer_id, CustomerId) else CustomerId(customer_id),
                    workflow=workflow,
                    sop_branch=_resolve_sop_branch(result["sop_branch"]) if result.get("sop_branch") else None,
                    customer_rules_applied=list(customer_config_dict.keys()),
                    tool_calls=tool_calls,
                    memory_operations=memory_operations,
                    state_before=load.current_state if isinstance(load.current_state, LoadState) else LoadState(load.current_state),
                    state_after=LoadState(state_after) if state_after else None,
                    status="completed",
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )
                await self._agent_run_repo.save(agent_run)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to save agent run: {e}", exc_info=True)

        # 8. Return results
        return {
            "run_id": run_id,
            "event_id": event_id,
            "load_id": load_id,
            "workflow": workflow,
            "sop_branch": result.get("sop_branch"),
            "branch_reason": result.get("branch_reason"),
            "customer_rules_applied": list(customer_config_dict.keys()),
            "tool_calls": result.get("tool_calls", []),
            "memory_operations": result.get("memory_operations", []),
            "state_before": load.current_state if isinstance(load.current_state, str) else load.current_state.value,
            "state_after": state_after,
            "actions_taken": result.get("actions_taken", []),
            "status": "completed",
        }

    async def get_workflow(self, workflow: str) -> Any:
        """Get a compiled workflow by name.

        Args:
            workflow: The workflow name.

        Returns:
            The compiled LangGraph workflow.
        """
        return self._workflows.get(workflow)