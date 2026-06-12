"""Monitoring and metrics routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import DatabaseManager
from src.infrastructure.repositories import (
    get_load_repository,
    get_agent_run_repository,
    get_memory_repository,
)
from src.application.dto import (
    AgentRunSummary,
    MemoryMetrics,
    FailureSummary,
    ScheduledFollowUp,
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


@router.get("/dashboard")
async def get_dashboard(session: AsyncSession = Depends(get_db_session)):
    """Get the monitoring dashboard data.

    Returns a summary matching the DashboardStats interface:
    active_loads, running_agents, failed_agents, scheduled_followups,
    open_issues, active_tasks, agent_runs_24h, memory_operations_24h, error_rate_24h
    """
    if session is None:
        return {
            "active_loads": 0,
            "running_agents": 0,
            "failed_agents": 0,
            "scheduled_followups": 0,
            "open_issues": 0,
            "active_tasks": 0,
            "agent_runs_24h": 0,
            "memory_operations_24h": 0,
            "error_rate_24h": 0.0,
        }

    load_repo = get_load_repository(session)
    agent_run_repo = get_agent_run_repository(session)

    active_loads_list = await load_repo.get_active_loads()
    recent_runs = await agent_run_repo.get_recent_runs(limit=100)

    # Count by status
    running_count = sum(1 for r in recent_runs if r.status == "running")
    failed_count = sum(1 for r in recent_runs if r.status in ("failed", "error"))
    completed_count = sum(1 for r in recent_runs if r.status == "completed")

    # Calculate error rate
    total_runs = len(recent_runs) if recent_runs else 1
    error_rate = round((failed_count / total_runs) * 100, 1) if total_runs > 0 else 0.0

    return {
        "active_loads": len(active_loads_list),
        "running_agents": running_count,
        "failed_agents": failed_count,
        "scheduled_followups": 0,
        "open_issues": 0,
        "active_tasks": running_count,
        "agent_runs_24h": len(recent_runs),
        "memory_operations_24h": 0,
        "error_rate_24h": error_rate,
    }


@router.get("/agent-runs", response_model=list[AgentRunSummary])
async def get_agent_runs(
    load_id: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
):
    """Get recent agent runs, optionally filtered by load ID."""
    if session is None:
        return []

    agent_run_repo = get_agent_run_repository(session)

    if load_id:
        runs = await agent_run_repo.get_by_load_id(load_id)
    else:
        runs = await agent_run_repo.get_recent_runs(limit=limit)

    return [
        AgentRunSummary(
            run_id=r.run_id,
            event_id=r.event_id,
            load_id=r.load_id,
            customer_id=r.customer_id,
            workflow=r.workflow,
            sop_branch=r.sop_branch,
            tool_calls_count=len(r.tool_calls) if r.tool_calls else 0,
            memory_operations_count=len(r.memory_operations) if r.memory_operations else 0,
            state_before=r.state_before,
            state_after=r.state_after,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at,
        )
        for r in runs[:limit]
    ]


@router.get("/memory-metrics", response_model=MemoryMetrics)
async def get_memory_metrics(
    scope: str = "global",
    scope_id: str = "all",
    session: AsyncSession = Depends(get_db_session),
):
    """Get memory system metrics."""
    from src.domain.enums import MemoryScope

    memory_repo = get_memory_repository(session)
    metrics = await memory_repo.get_metrics(
        scope=MemoryScope(scope),
        scope_id=scope_id,
    )

    return MemoryMetrics(
        total_memories=metrics.get("total_memories", 0),
        by_type=metrics.get("by_type", {}),
        avg_confidence=metrics.get("avg_confidence", 0),
        avg_relevance=metrics.get("avg_relevance", 0),
        total_access_count=metrics.get("total_access_count", 0),
    )


@router.get("/failures", response_model=list[FailureSummary])
async def get_failures(
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
):
    """Get recent failure summaries."""
    # This would query for failed agent runs
    return []


@router.get("/scheduled-followups", response_model=list[ScheduledFollowUp])
async def get_scheduled_followups(
    load_id: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    """Get scheduled follow-up timers."""
    # This would query the timer table
    return []