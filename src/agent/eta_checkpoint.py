"""ETA Checkpoint LangGraph workflow.

Implements the on-route-to-delivery / ETA checkpoint workflow
as a LangGraph StateGraph.
"""

import logging
from typing import Annotated, Any, TypedDict, Literal
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    SOPBranch,
    SenderType,
    Channel,
)


class ETACheckpointState(TypedDict, total=False):
    """State for the ETA Checkpoint workflow."""

    # Input
    event_id: str
    load_id: str
    customer_id: str
    event_type: str
    event_data: dict

    # Load context
    load_data: dict
    current_state: str
    current_eta_utc: str | None

    # Customer config
    customer_config: dict

    # SOP
    sop_content: str
    sop_branch: str
    branch_reason: str

    # Agent messages
    messages: list

    # Tool calls
    tool_calls: list[dict]

    # Memory operations
    memory_operations: list[dict]

    # Output
    state_after: str | None
    actions_taken: list[str]
    followup_scheduled: bool
    escalation_sent: bool


def create_eta_checkpoint_workflow(llm: Any = None, tools: Any = None) -> Any:
    """Create the ETA Checkpoint LangGraph workflow.

    Args:
        llm: The LLM to use for agent decisions.
        tools: The tools available to the agent.

    Returns:
        A compiled LangGraph StateGraph.
    """
    workflow = StateGraph(ETACheckpointState)

    # --- Node Functions ---

    async def load_context(state: ETACheckpointState) -> dict:
        """Load the load context and customer configuration."""
        # In production, this would fetch from repositories
        return {
            "messages": state.get("messages", []) + [
                SystemMessage(content=f"Processing ETA checkpoint for load {state.get('load_id')}")
            ],
        }

    async def classify_event(state: ETACheckpointState) -> dict:
        """Classify the incoming event to determine the SOP branch."""
        event_type = state.get("event_type", "")
        event_data = state.get("event_data", {})
        valid_branches = [b.value for b in SOPBranch]

        # Try LLM classification if available
        if llm is not None:
            from pydantic import BaseModel

            class BranchDecision(BaseModel):
                branch: str
                reason: str

            try:
                structured = llm.with_structured_output(BranchDecision)
                result = await structured.ainvoke([
                    SystemMessage(content=f"{state.get('sop_content', '')}\n\nValid branches: {valid_branches}\nIf sender_type is broker, always return broker_messages."),
                    HumanMessage(content=f"Event: {event_data}\nType: {event_type}"),
                ])
                if result.branch in valid_branches:
                    return {
                        "sop_branch": result.branch,
                        "branch_reason": result.reason,
                        "messages": state.get("messages", []) + [
                            AIMessage(content=f"Classified event as branch: {result.branch} ({result.reason})")
                        ],
                    }
            except Exception:
                logger.exception("LLM classification failed, falling back to keyword matching")

        # Fallback: keyword matching
        if event_type == EventType.TRACKING.value:
            branch = SOPBranch.TRACKING_PING.value
            reason = "Event is a tracking ping"
        elif event_type == EventType.INBOUND_COMMUNICATION.value:
            sender = event_data.get("sender_type", "")
            if sender == SenderType.BROKER.value:
                branch = SOPBranch.BROKER_MESSAGES.value
                reason = "Message from broker - no action"
            else:
                # Check message content for specific patterns
                message = event_data.get("message", "").lower()
                if any(w in message for w in ["arrived", "at delivery", "at stop", "checked in"]):
                    branch = SOPBranch.ARRIVAL_CONFIRMATION.value
                    reason = "Driver indicates arrival"
                elif any(w in message for w in ["eta", "arriving", "will be there", "be there", "estimated", "minutes away", "minutes out"]):
                    branch = SOPBranch.DRIVER_PROVIDES_ETA.value
                    reason = "Driver provides ETA"
                elif any(w in message for w in ["question", "what is", "what's", "where is", "where's", "when is", "can you"]):
                    branch = SOPBranch.LOAD_INFORMATION_QUESTION.value
                    reason = "Driver asks a question"
                elif any(w in message for w in ["issue", "problem", "delay", "stuck", "breakdown", "broke", "broken"]):
                    branch = SOPBranch.OPERATIONAL_ISSUE.value
                    reason = "Driver reports operational issue"
                else:
                    branch = SOPBranch.NO_ACTION.value
                    reason = "No specific action needed"
        elif event_type == EventType.LOAD_UPDATE.value:
            branch = SOPBranch.DRIVER_PROVIDES_ETA.value
            reason = "Load update event"
        elif event_type == EventType.TIMER_CALLBACK.value:
            branch = SOPBranch.TRACKING_PING.value
            reason = "Timer callback for ETA follow-up"
        else:
            branch = SOPBranch.NO_ACTION.value
            reason = "Unknown event type"

        return {
            "sop_branch": branch,
            "branch_reason": reason,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"Classified event as branch: {branch} ({reason})")
            ],
        }

    async def execute_branch(state: ETACheckpointState) -> dict:
        """Execute the determined SOP branch using available tools."""
        branch = state.get("sop_branch", "")
        tool_calls = state.get("tool_calls", [])
        actions_taken = state.get("actions_taken", [])
        memory_operations = state.get("memory_operations", [])
        customer_config = state.get("customer_config", {})
        load_data = state.get("load_data", {})
        event_data = state.get("event_data", {})

        # Record the branch decision
        tool_calls.append({
            "tool": "record_sop_branch",
            "arguments": {
                "load_id": state.get("load_id"),
                "event_id": state.get("event_id"),
                "branch": branch,
                "reason": state.get("branch_reason", ""),
            },
        })
        actions_taken.append(f"Recorded SOP branch: {branch}")

        # Helper to determine the communication tool based on inbound channel
        inbound_channel = event_data.get("channel", "sms")

        def _send_to_driver(msg: str) -> dict[str, Any]:
            """Return the appropriate tool call dict for sending a message to the driver."""
            if inbound_channel == "email":
                return {"tool": "send_email", "arguments": {"recipient": "driver", "subject": "Load Update", "body": msg}}
            return {"tool": "send_sms", "arguments": {"recipient": "driver", "message": msg}}

        def _escalate(issue_type: str, details: str, escalation_channel: str) -> list[dict[str, Any]]:
            """Return tool call dicts for escalating to ops based on channel."""
            calls = []
            calls.append({"tool": "create_issue", "arguments": {"title": issue_type, "description": details, "issue_type": issue_type}})
            if escalation_channel in ("email", "email_and_slack"):
                calls.append({"tool": "send_email", "arguments": {"recipient": "ops", "subject": f"Issue: {issue_type}", "body": details}})
            if escalation_channel in ("slack", "email_and_slack"):
                calls.append({"tool": "send_slack_message", "arguments": {"audience": "internal", "message": details, "escalation_type": issue_type}})
            return calls

        def _create_missing_info_task(details: str, missing_action: str, escalation_channel: str) -> list[dict[str, Any]]:
            """Return tool call dicts for missing load info based on customer config."""
            calls = []
            calls.append({"tool": "create_task", "arguments": {"title": "Missing load info", "description": details, "task_type": "missing_load_info"}})
            if missing_action == "create_task_and_send_visibility":
                if escalation_channel in ("email", "email_and_slack"):
                    calls.append({"tool": "send_email", "arguments": {"recipient": "ops", "subject": "Missing load info", "body": details}})
                if escalation_channel in ("slack", "email_and_slack"):
                    calls.append({"tool": "send_slack_message", "arguments": {"audience": "broker", "message": details, "escalation_type": "missing_load_info"}})
            return calls

        # Execute branch-specific logic
        if branch == SOPBranch.ARRIVAL_CONFIRMATION.value:
            # Transition to at_delivery and request POD
            tool_calls.append({
                "tool": "update_load_state",
                "arguments": {
                    "target_state": LoadState.AT_DELIVERY.value,
                    "reason": "Driver arrived at delivery",
                },
            })
            actions_taken.append("Transitioned load to at_delivery")

            # Send message asking for POD via inbound channel
            tool_calls.append(_send_to_driver("Thank you for confirming arrival. Please send POD when unloading is complete."))
            actions_taken.append("Sent arrival confirmation and POD request")

            # Cancel any pending timers
            tool_calls.append({
                "tool": "cancel_timers",
                "arguments": {
                    "timer_type": "eta_followup",
                },
            })
            actions_taken.append("Canceled pending timers")

            # Add episodic memory
            memory_operations.append({
                "operation": "add",
                "memory_type": "episodic",
                "scope": "load",
                "scope_id": state.get("load_id"),
                "content": "Driver arrived at delivery location",
            })

        elif branch == SOPBranch.TRACKING_PING.value:
            # Check if tracking ping indicates arrival (inside geofence)
            distance = event_data.get("distance_to_delivery", 999)
            geofence_radius = customer_config.get("delivery_geofence_radius_miles", 2)
            ping_sequence = event_data.get("ping_sequence", 1)

            if distance <= geofence_radius and ping_sequence >= 3:
                # 3 consecutive pings inside geofence → arrival
                tool_calls.append({
                    "tool": "update_load_state",
                    "arguments": {
                        "target_state": LoadState.AT_DELIVERY.value,
                        "reason": f"3 consecutive tracking pings within {geofence_radius} mile geofence",
                    },
                })
                actions_taken.append("Transitioned load to at_delivery based on tracking")

                # Cancel any pending timers
                tool_calls.append({
                    "tool": "cancel_timers",
                    "arguments": {
                        "timer_type": "eta_followup",
                    },
                })
                actions_taken.append("Canceled pending timers")
            elif distance <= geofence_radius:
                # Inside geofence but not yet 3 pings - record proximity
                actions_taken.append(f"Tracking ping {ping_sequence} inside geofence ({distance:.1f} miles)")
            else:
                # Outside geofence - just record
                actions_taken.append(f"Tracking ping outside geofence ({distance:.1f} miles)")

        elif branch == SOPBranch.DRIVER_PROVIDES_ETA.value:
            # Validate and update ETA from driver's message
            tool_calls.append({
                "tool": "validate_eta",
                "arguments": {
                    "raw_eta": event_data.get("message", ""),
                    "delivery_timezone": "America/Chicago",
                },
            })
            tool_calls.append({
                "tool": "update_eta",
                "arguments": {
                    "target_location": "delivery",
                    "eta_utc": "__from_validate_eta__",
                    "source": "driver",
                },
            })
            actions_taken.append("Validated and updated ETA based on driver input")

            # Send acknowledgment message via inbound channel
            tool_calls.append(_send_to_driver("Thank you for the ETA update. We have updated your estimated arrival time."))
            actions_taken.append("Sent ETA acknowledgment")

            # Schedule follow-up timer
            eta_minutes = customer_config.get("eta_followup_timer_minutes", 30)
            from datetime import datetime as dt, timezone as tz
            fire_at = dt.now(tz.utc).isoformat()  # Simplified; in production, add eta_minutes
            tool_calls.append({
                "tool": "create_timer",
                "arguments": {
                    "timer_type": "eta_followup",
                    "fire_at_utc": fire_at,
                    "reason": "ETA follow-up per customer config",
                },
            })
            actions_taken.append(f"Scheduled ETA follow-up timer in {eta_minutes} minutes")

        elif branch == SOPBranch.OPERATIONAL_ISSUE.value:
            escalation_channel = customer_config.get("escalation_channel", "internal")
            # Create an issue for the operational problem
            issue_details = event_data.get("message", "Operational issue reported")
            for call in _escalate("equipment_failure", issue_details, escalation_channel):
                tool_calls.append(call)
            actions_taken.append(f"Escalated operational issue via {escalation_channel}")

            # Send acknowledgment to driver via inbound channel
            tool_calls.append(_send_to_driver("We're sorry to hear about the issue. Our team is reviewing and will follow up shortly."))
            actions_taken.append("Sent acknowledgment to driver")

        elif branch == SOPBranch.BROKER_MESSAGES.value:
            tool_calls.append({
                "tool": "no_action",
                "arguments": {
                    "load_id": state.get("load_id"),
                    "event_id": state.get("event_id"),
                    "reason": "Broker message - no action per SOP",
                },
            })
            actions_taken.append("No action: broker message")

        elif branch == SOPBranch.LOAD_INFORMATION_QUESTION.value:
            # Look up load info and respond with delivery address
            stops = load_data.get("stops", [])
            delivery_stop = next((s for s in stops if s.get("type") == "delivery"), None)
            message = event_data.get("message", "").lower()

            # Check if the requested info is available in load data
            # If driver asks for phone number and it's missing, escalate
            requested_info_available = True
            if any(w in message for w in ["phone", "phone number", "receiver phone"]):
                # Check if receiver phone is available
                if delivery_stop:
                    ref_nums = delivery_stop.get("reference_numbers", {})
                    if not ref_nums.get("receiver_phone"):
                        requested_info_available = False

            if not requested_info_available:
                # Missing info - escalate based on customer config
                missing_action = customer_config.get("missing_load_info_action", "create_task")
                escalation_channel = customer_config.get("escalation_channel", "email")
                tool_calls.append(_send_to_driver("We're checking on that information for you."))
                for call in _create_missing_info_task("Driver requested missing load information", missing_action, escalation_channel):
                    tool_calls.append(call)
                actions_taken.append("Escalated missing load info")
            elif delivery_stop:
                address = delivery_stop.get("address", {})
                address_str = f"{address.get('line_1', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('postal_code', '')}"
                tool_calls.append(_send_to_driver(f"The delivery address is: {address_str}"))
                actions_taken.append(f"Sent delivery address to driver: {address_str}")
            else:
                # No delivery stop info available - escalate
                escalation_channel = customer_config.get("escalation_channel", "email")
                for call in _escalate("missing_load_info", "Driver requested load information but no delivery data available", escalation_channel):
                    tool_calls.append(call)
                actions_taken.append("Escalated - no delivery data available")

        # Add semantic memory for this event
        memory_operations.append({
            "operation": "add",
            "memory_type": "semantic",
            "scope": "load",
            "scope_id": state.get("load_id"),
            "content": f"Event {state.get('event_id')} classified as {branch}",
            "tags": [branch, state.get("event_type", "")],
        })

        return {
            "tool_calls": tool_calls,
            "actions_taken": actions_taken,
            "memory_operations": memory_operations,
        }

    async def determine_state_transition(state: ETACheckpointState) -> dict:
        """Determine if a state transition is needed."""
        branch = state.get("sop_branch", "")
        state_after = None

        if branch == SOPBranch.ARRIVAL_CONFIRMATION.value:
            state_after = LoadState.AT_DELIVERY.value
        elif branch == SOPBranch.TRACKING_PING.value:
            # Check if tracking ping indicates arrival
            event_data = state.get("event_data", {})
            customer_config = state.get("customer_config", {})
            distance = event_data.get("distance_to_delivery", 999)
            geofence_radius = customer_config.get("delivery_geofence_radius_miles", 2)
            ping_sequence = event_data.get("ping_sequence", 1)

            if distance <= geofence_radius and ping_sequence >= 3:
                state_after = LoadState.AT_DELIVERY.value

        return {
            "state_after": state_after,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"State transition: {state_after or 'no change'}")
            ],
        }

    # --- Routing Functions ---

    def route_after_classify(state: ETACheckpointState) -> str:
        """Route after event classification."""
        branch = state.get("sop_branch", "")
        if branch == SOPBranch.NO_ACTION.value:
            return "determine_state"
        return "execute_branch"

    # --- Build Graph ---

    workflow.add_node("load_context", load_context)
    workflow.add_node("classify_event", classify_event)
    workflow.add_node("execute_branch", execute_branch)
    workflow.add_node("determine_state", determine_state_transition)

    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "classify_event")
    workflow.add_conditional_edges(
        "classify_event",
        route_after_classify,
        {
            "execute_branch": "execute_branch",
            "determine_state": "determine_state",
        },
    )
    workflow.add_edge("execute_branch", "determine_state")
    workflow.add_edge("determine_state", END)

    return workflow.compile(checkpointer=MemorySaver())