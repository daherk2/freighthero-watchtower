"""Agent debugger routes.

Provides endpoints for inspecting agent behavior, memory state,
and workflow execution details.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import MemoryScope, MemoryType
from src.infrastructure.database import DatabaseManager
from src.infrastructure.repositories import (
    get_agent_run_repository,
    get_memory_repository,
    get_load_repository,
    get_event_repository,
    get_tool_call_repository,
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


@router.get("/agent-runs/{run_id}")
async def get_agent_run_detail(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about an agent run.

    Includes the full execution trace, tool calls, memory operations,
    and state transitions.
    """
    if session is None:
        raise HTTPException(status_code=503, detail="Database not configured")

    agent_run_repo = get_agent_run_repository(session)

    try:
        run = await agent_run_repo.get_by_id(run_id)
        return {
            "run_id": run.run_id,
            "event_id": run.event_id,
            "load_id": run.load_id,
            "customer_id": run.customer_id if isinstance(run.customer_id, str) else run.customer_id.value,
            "workflow": run.workflow,
            "sop_branch": run.sop_branch,
            "customer_rules_applied": run.customer_rules_applied,
            "tool_calls": run.tool_calls,
            "memory_operations": run.memory_operations,
            "state_before": run.state_before if isinstance(run.state_before, str) else run.state_before.value if run.state_before else None,
            "state_after": run.state_after if isinstance(run.state_after, str) else run.state_after.value if run.state_after else None,
            "status": run.status,
            "error": run.error,
            "trace_id": run.trace_id,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Agent run {run_id} not found")


@router.get("/loads/{load_id}/history")
async def get_load_history(
    load_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get the full history for a load.

    Includes all events, agent runs, tool calls, and memory operations.
    """
    if session is None:
        raise HTTPException(status_code=503, detail="Database not configured")

    load_repo = get_load_repository(session)
    event_repo = get_event_repository(session)
    agent_run_repo = get_agent_run_repository(session)
    tool_call_repo = get_tool_call_repository(session)

    try:
        load = await load_repo.get_by_id(load_id)
        events = await event_repo.get_by_load_id(load_id)
        runs = await agent_run_repo.get_by_load_id(load_id)
        tool_calls = await tool_call_repo.get_by_load_id(load_id)

        return {
            "load": {
                "load_id": load.load_id,
                "customer_id": load.customer_id if isinstance(load.customer_id, str) else load.customer_id.value,
                "current_state": load.current_state if isinstance(load.current_state, str) else load.current_state.value,
                "current_eta_utc": load.current_eta_utc,
            },
            "events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type if isinstance(e.event_type, str) else e.event_type.value,
                    "occurred_at": e.occurred_at,
                }
                for e in events
            ],
            "agent_runs": [
                {
                    "run_id": r.run_id,
                    "workflow": r.workflow,
                    "sop_branch": r.sop_branch,
                    "status": r.status,
                    "started_at": r.started_at,
                }
                for r in runs
            ],
            "tool_calls": [
                {
                    "tool_call_id": tc.tool_call_id,
                    "tool": tc.tool,
                    "arguments": tc.arguments,
                    "result": tc.result,
                }
                for tc in tool_calls
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Load {load_id} not found")


@router.get("/memory/{scope}/{scope_id}")
async def get_memory_state(
    scope: str,
    scope_id: str,
    memory_type: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
):
    """Get the current memory state for a given scope.

    Args:
        scope: Memory scope (load, customer, global).
        scope_id: Identifier within the scope.
        memory_type: Optional filter by memory type.
        limit: Maximum number of results.
    """
    memory_repo = get_memory_repository(session)

    memories = await memory_repo.retrieve(
        scope=MemoryScope(scope),
        scope_id=scope_id,
        memory_type=MemoryType(memory_type) if memory_type else None,
        limit=limit,
    )

    return {
        "scope": scope,
        "scope_id": scope_id,
        "memories": memories,
        "count": len(memories),
    }


@router.post("/memory/add")
async def add_memory_entry(
    memory_type: str,
    scope: str,
    scope_id: str,
    content: str,
    tags: list[str] | None = None,
    confidence: float = 1.0,
    content_type: str = "fact",
    session: AsyncSession = Depends(get_db_session),
):
    """Manually add a memory entry (for debugging)."""
    memory_repo = get_memory_repository(session)

    memory_id = await memory_repo.add(
        memory_type=MemoryType(memory_type),
        scope=MemoryScope(scope),
        scope_id=scope_id,
        content=content,
        tags=tags,
        confidence=confidence,
        content_type=content_type,
    )

    await session.commit()

    return {"memory_id": memory_id, "status": "added"}


@router.delete("/memory/{memory_id}")
async def delete_memory_entry(
    memory_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a memory entry (for debugging)."""
    memory_repo = get_memory_repository(session)

    await memory_repo.delete(memory_id)
    await session.commit()

    return {"memory_id": memory_id, "status": "deleted"}


@router.get("/workflows")
async def list_workflows():
    """List available agent workflows."""
    return {
        "workflows": [
            {
                "name": "delivery_eta_checkpoint",
                "description": "Monitor delivery ETA, tracking, arrival, and operational exceptions",
                "states": ["dispatched", "on_route_to_delivery"],
            },
            {
                "name": "confirm_delivery",
                "description": "Confirm unloading, collect POD, handle lumper receipts",
                "states": ["at_delivery", "confirm_delivery"],
            },
        ]
    }


@router.post("/workflows/{workflow}/test")
async def test_workflow(
    workflow: str,
    event_data: dict,
    session: AsyncSession = Depends(get_db_session),
):
    """Test a workflow with sample input (for debugging).

    Args:
        workflow: The workflow name.
        event_data: Sample event data to process.
    """
    from src.agent.orchestrator import AgentOrchestrator

    load_repo = get_load_repository(session)
    event_repo = get_event_repository(session)
    agent_run_repo = get_agent_run_repository(session)

    orchestrator = AgentOrchestrator(
        load_repo=load_repo,
        event_repo=event_repo,
        agent_run_repo=agent_run_repo,
    )

    workflow_graph = await orchestrator.get_workflow(workflow)
    if workflow_graph is None:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow} not found")

    # Run the workflow with test data
    config = {"configurable": {"thread_id": f"test-{datetime.now(timezone.utc).isoformat()}"}}
    result = await workflow_graph.ainvoke(event_data, config)

    return result