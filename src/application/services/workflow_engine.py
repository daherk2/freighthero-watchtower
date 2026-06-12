"""Workflow Engine service.

Orchestrates the execution of agent workflows, managing the
lifecycle from event ingestion to completion.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from src.domain.enums import CustomerId, EventType, LoadState
from src.domain.exceptions import LoadNotFoundError
from src.domain.models import AgentRun, Event
from src.application.ports import (
    AgentRunRepository,
    EventRepository,
    LoadRepository,
    MemoryRepository,
    ToolCallRepository,
)
from src.application.services.customer_resolver import CustomerBehaviorResolver
from src.application.services.sop_compiler import SOPCompiler


class WorkflowEngine:
    """Orchestrates agent workflow execution.

    The WorkflowEngine manages the full lifecycle of processing an event:
    1. Load the event and current load state
    2. Resolve customer behavior configuration
    3. Compile the SOP with customer-specific rules
    4. Initialize the agent run
    5. Execute the LangGraph workflow
    6. Record results and state transitions
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
    ):
        self._load_repo = load_repo
        self._event_repo = event_repo
        self._agent_run_repo = agent_run_repo
        self._memory_repo = memory_repo
        self._tool_call_repo = tool_call_repo
        self._customer_resolver = customer_resolver or CustomerBehaviorResolver()
        self._sop_compiler = sop_compiler or SOPCompiler(self._customer_resolver)

    async def execute(
        self,
        event_id: str,
        load_id: str,
        workflow: str,
    ) -> AgentRun:
        """Execute a workflow for an event.

        Args:
            event_id: The event to process.
            load_id: The load context.
            workflow: The workflow to execute.

        Returns:
            The completed AgentRun record.
        """
        # 1. Load context
        event = await self._event_repo.get_by_id(event_id)
        load = await self._load_repo.get_by_id(load_id)
        customer_id = CustomerId(load.customer_id) if isinstance(load.customer_id, str) else load.customer_id

        # 2. Create agent run record
        run_id = str(uuid.uuid4())
        agent_run = AgentRun(
            run_id=run_id,
            event_id=event_id,
            load_id=load_id,
            customer_id=customer_id,
            workflow=workflow,
            state_before=load.current_state,
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        await self._agent_run_repo.save(agent_run)

        try:
            # 3. Resolve customer config
            customer_config = await self._customer_resolver.get_config(customer_id)

            # 4. Compile SOP
            sop_content = await self._sop_compiler.get_sop(workflow, customer_id)

            # 5. Execute the LangGraph workflow (delegated to agent layer)
            # This will be implemented in the agent orchestrator
            from src.agent.orchestrator import AgentOrchestrator

            orchestrator = AgentOrchestrator(
                load_repo=self._load_repo,
                event_repo=self._event_repo,
                agent_run_repo=self._agent_run_repo,
                memory_repo=self._memory_repo,
                tool_call_repo=self._tool_call_repo,
                customer_resolver=self._customer_resolver,
                sop_compiler=self._sop_compiler,
            )

            result = await orchestrator.run(
                event_id=event_id,
                load_id=load_id,
                workflow=workflow,
            )

            # 6. Update agent run with results
            agent_run.status = "completed"
            agent_run.sop_branch = result.get("sop_branch")
            agent_run.customer_rules_applied = result.get("customer_rules_applied", [])
            agent_run.tool_calls = result.get("tool_calls", [])
            agent_run.memory_operations = result.get("memory_operations", [])
            agent_run.state_after = result.get("state_after")
            agent_run.completed_at = datetime.now(timezone.utc).isoformat()

            await self._agent_run_repo.update_status(
                run_id=run_id,
                status="completed",
            )

            return agent_run

        except Exception as e:
            # Update agent run with error
            await self._agent_run_repo.update_status(
                run_id=run_id,
                status="failed",
                error=str(e),
            )
            raise

    async def get_run(self, run_id: str) -> AgentRun:
        """Get an agent run by ID."""
        return await self._agent_run_repo.get_by_id(run_id)

    async def get_runs_for_load(self, load_id: str) -> list[AgentRun]:
        """Get all agent runs for a load."""
        return await self._agent_run_repo.get_by_load_id(load_id)