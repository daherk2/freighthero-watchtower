"""Confirm Delivery LangGraph workflow.

Implements the confirm delivery workflow as a LangGraph StateGraph.
"""

from typing import Annotated, TypedDict, Literal
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    ConfirmDeliveryBranch,
    SenderType,
    AttachmentCategory,
)


class ConfirmDeliveryState(TypedDict, total=False):
    """State for the Confirm Delivery workflow."""

    # Input
    event_id: str
    load_id: str
    customer_id: str
    event_type: str
    event_data: dict

    # Load context
    load_data: dict
    current_state: str

    # Customer config
    customer_config: dict

    # SOP
    sop_content: str
    sop_branch: str
    branch_reason: str

    # Attachment handling
    attachment_classifications: list[dict]
    pod_received: bool
    lumper_received: bool

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
    pod_status: str  # collected, pending, not_applicable


def create_confirm_delivery_workflow(llm=None, tools=None):
    """Create the Confirm Delivery LangGraph workflow.

    Args:
        llm: The LLM to use for agent decisions.
        tools: The tools available to the agent.

    Returns:
        A compiled LangGraph StateGraph.
    """
    workflow = StateGraph(ConfirmDeliveryState)

    # --- Node Functions ---

    async def load_context(state: ConfirmDeliveryState) -> dict:
        """Load the load context and customer configuration."""
        return {
            "messages": state.get("messages", []) + [
                SystemMessage(content=f"Processing confirm delivery for load {state.get('load_id')}")
            ],
            "pod_received": False,
            "lumper_received": False,
            "attachment_classifications": [],
        }

    async def classify_event(state: ConfirmDeliveryState) -> dict:
        """Classify the incoming event to determine the SOP branch."""
        event_type = state.get("event_type", "")
        event_data = state.get("event_data", {})
        valid_branches = [b.value for b in ConfirmDeliveryBranch]

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
                pass  # Fall through to keyword matching

        # Check for broker messages first
        if event_type == EventType.INBOUND_COMMUNICATION.value:
            sender = event_data.get("sender_type", "")
            if sender == SenderType.BROKER.value:
                return {
                    "sop_branch": ConfirmDeliveryBranch.BROKER_MESSAGES.value,
                    "branch_reason": "Message from broker - no action",
                }

        # Check for attachments
        attachments = event_data.get("attachments", [])
        if attachments:
            # Process attachments
            classifications = []
            for att in attachments:
                # Check both direct classification and mock_classification
                att_type = att.get("classification", "").lower()
                mock_categories = att.get("mock_classification", {}).get("categories", [])
                mock_desc = att.get("mock_classification", {}).get("description", "").lower()
                file_name = att.get("file_name", "").lower()

                # Determine attachment type from multiple sources
                is_pod = (
                    att_type in ["pod", "proof_of_delivery", "delivery_receipt"]
                    or "document_pod" in mock_categories
                    or "pod" in mock_categories
                    or "pod" in file_name
                    or "proof of delivery" in mock_desc
                )
                is_lumper = (
                    att_type in ["lumper", "lumper_receipt", "receipt"]
                    or "lumper_receipt" in mock_categories
                    or "lumper" in mock_categories
                    or "lumper" in file_name
                    or "lumper" in mock_desc
                )

                if is_pod:
                    classifications.append({
                        "type": "pod",
                        "url": att.get("url", ""),
                        "attachment_id": att.get("attachment_id", ""),
                        "confidence": 0.9,
                    })
                elif is_lumper:
                    classifications.append({
                        "type": "lumper_receipt",
                        "url": att.get("url", ""),
                        "attachment_id": att.get("attachment_id", ""),
                        "confidence": 0.9,
                    })
                else:
                    classifications.append({
                        "type": "other",
                        "url": att.get("url", ""),
                        "attachment_id": att.get("attachment_id", ""),
                        "confidence": 0.5,
                    })

            if any(c["type"] == "pod" for c in classifications):
                return {
                    "sop_branch": ConfirmDeliveryBranch.POD_DOCUMENT.value,
                    "branch_reason": "POD document received",
                    "attachment_classifications": classifications,
                    "pod_received": True,
                }
            elif any(c["type"] == "lumper_receipt" for c in classifications):
                return {
                    "sop_branch": ConfirmDeliveryBranch.LUMPER_RECEIPT.value,
                    "branch_reason": "Lumper receipt received",
                    "attachment_classifications": classifications,
                    "lumper_received": True,
                }
            else:
                return {
                    "sop_branch": ConfirmDeliveryBranch.OTHER_ATTACHMENT.value,
                    "branch_reason": "Unrecognized or unreadable attachment",
                    "attachment_classifications": classifications,
                }

        # Check message content for delivery status
        message = event_data.get("message", "").lower() if event_type == EventType.INBOUND_COMMUNICATION.value else ""

        if any(w in message for w in ["unloaded", "empty", "delivered", "done", "finished"]):
            # Check if POD was already received
            if state.get("pod_received", False):
                return {
                    "sop_branch": ConfirmDeliveryBranch.POD_DOCUMENT.value,
                    "branch_reason": "Delivery confirmed with POD already received",
                }
            return {
                "sop_branch": ConfirmDeliveryBranch.DELIVERED_WITHOUT_POD.value,
                "branch_reason": "Driver confirms delivery without POD",
            }

        if any(w in message for w in ["unloading", "started unloading", "beginning to unload"]):
            return {
                "sop_branch": ConfirmDeliveryBranch.UNLOADING_STARTED.value,
                "branch_reason": "Driver reports unloading started",
            }

        if any(w in message for w in ["not started", "haven't started", "waiting to unload"]):
            return {
                "sop_branch": ConfirmDeliveryBranch.UNLOADING_NOT_STARTED.value,
                "branch_reason": "Driver reports unloading not started",
            }

        if any(w in message for w in ["issue", "problem", "delay", "stuck"]):
            return {
                "sop_branch": ConfirmDeliveryBranch.OPERATIONAL_ISSUE.value,
                "branch_reason": "Driver reports operational issue",
            }

        # First arrival contact
        if event_type == EventType.TRACKING.value:
            return {
                "sop_branch": ConfirmDeliveryBranch.FIRST_ARRIVAL_CONTACT.value,
                "branch_reason": "Tracking indicates arrival at delivery",
            }

        return {
            "sop_branch": ConfirmDeliveryBranch.NO_ACTION.value,
            "branch_reason": "No specific action needed",
        }

    async def execute_branch(state: ConfirmDeliveryState) -> dict:
        """Execute the determined SOP branch using available tools."""
        branch = state.get("sop_branch", "")
        tool_calls = state.get("tool_calls", [])
        actions_taken = state.get("actions_taken", [])
        memory_operations = state.get("memory_operations", [])
        customer_config = state.get("customer_config", {})
        event_data = state.get("event_data", {})

        # Helper to determine the communication tool based on inbound channel
        inbound_channel = event_data.get("channel", "sms")

        def _send_to_driver(msg: str):
            """Return the appropriate tool call dict for sending a message to the driver."""
            if inbound_channel == "email":
                return {"tool": "send_email", "arguments": {"recipient": "driver", "subject": "Load Update", "body": msg}}
            return {"tool": "send_sms", "arguments": {"recipient": "driver", "message": msg}}

        def _escalate(issue_type: str, details: str, escalation_channel: str):
            """Return tool call dicts for escalating to ops based on channel."""
            calls = []
            calls.append({"tool": "create_issue", "arguments": {"title": issue_type, "description": details, "issue_type": issue_type}})
            if escalation_channel in ("email", "email_and_slack"):
                calls.append({"tool": "send_email", "arguments": {"recipient": "ops", "subject": f"Issue: {issue_type}", "body": details}})
            if escalation_channel in ("slack", "email_and_slack"):
                calls.append({"tool": "send_slack_message", "arguments": {"audience": "internal", "message": details, "escalation_type": issue_type}})
            return calls

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

        # Execute branch-specific logic
        if branch == ConfirmDeliveryBranch.POD_DOCUMENT.value:
            # POD received - handle per customer config
            pod_validation = customer_config.get("pod_validation_type", "automatic")
            pod_visibility = customer_config.get("pod_received_visibility", "internal")

            # Check/classify the attachment
            attachments = state.get("attachment_classifications", [])
            att_id = ""
            if attachments:
                att_id = attachments[0].get("attachment_id", "")
            else:
                att_id = state.get("event_data", {}).get("attachments", [{}])[0].get("attachment_id", "")
            tool_calls.append({
                "tool": "check_attachment",
                "arguments": {
                    "attachment_id": att_id,
                },
            })
            actions_taken.append(f"POD received, validation type: {pod_validation}")

            # If customer requires human review, create a task
            if pod_validation == "human_review":
                tool_calls.append({
                    "tool": "create_task",
                    "arguments": {
                        "title": "POD review needed",
                        "description": "POD document received and requires human review",
                        "task_type": "pod_review",
                    },
                })
                actions_taken.append("Created POD review task")

            # Transition to pod_collected state
            tool_calls.append({
                "tool": "update_load_state",
                "arguments": {
                    "target_state": LoadState.POD_COLLECTED.value,
                    "reason": "POD document received",
                },
            })
            actions_taken.append("Transitioned load to pod_collected")

            # Send thank you message via inbound channel
            tool_calls.append(_send_to_driver("Thank you for sending the POD. Your delivery has been confirmed."))
            actions_taken.append("Sent POD confirmation to driver")

            # POD received visibility per customer config
            escalation_channel = customer_config.get("escalation_channel", "email")
            if pod_visibility == "notify_escalation_channel":
                if escalation_channel in ("email", "email_and_slack"):
                    tool_calls.append({"tool": "send_email", "arguments": {"recipient": "ops", "subject": "POD Received", "body": "POD has been received and validated for this load."}})
                if escalation_channel in ("slack", "email_and_slack"):
                    tool_calls.append({"tool": "send_slack_message", "arguments": {"audience": "broker", "message": "POD has been received and validated for this load.", "escalation_type": "pod_received"}})

            # Add episodic memory for POD
            memory_operations.append({
                "operation": "add",
                "memory_type": "episodic",
                "scope": "load",
                "scope_id": state.get("load_id"),
                "content": "POD document received and classified",
                "tags": ["pod", "delivery_confirmation"],
            })

        elif branch == ConfirmDeliveryBranch.LUMPER_RECEIPT.value:
            # Check the attachment
            attachments = state.get("attachment_classifications", [])
            att_id = attachments[0].get("attachment_id", "") if attachments else ""
            tool_calls.append({
                "tool": "check_attachment",
                "arguments": {
                    "attachment_id": att_id,
                },
            })
            actions_taken.append("Lumper receipt received")

            # Handle lumper receipt per customer config
            lumper_handling = customer_config.get("lumper_receipt_handling", "classify_and_create_review_task")
            if lumper_handling == "classify_and_create_review_task":
                tool_calls.append({
                    "tool": "create_task",
                    "arguments": {
                        "title": "Lumper receipt review",
                        "description": "Lumper receipt received and requires review",
                        "task_type": "lumper_review",
                    },
                })
                actions_taken.append("Created lumper review task")
            elif lumper_handling == "forward_email_if_lumper_else_review_task":
                # Customer C: forward email if lumper receipt via email, else create review task
                if inbound_channel == "email":
                    tool_calls.append({"tool": "forward_email", "arguments": {}})
                    actions_taken.append("Forwarded lumper receipt email to broker")
                else:
                    tool_calls.append({
                        "tool": "create_task",
                        "arguments": {
                            "title": "Lumper receipt review",
                            "description": "Lumper receipt received and requires review",
                            "task_type": "lumper_review",
                        },
                    })
                    actions_taken.append("Created lumper review task")

            memory_operations.append({
                "operation": "add",
                "memory_type": "episodic",
                "scope": "load",
                "scope_id": state.get("load_id"),
                "content": "Lumper receipt received",
                "tags": ["lumper", "receipt"],
            })

        elif branch == ConfirmDeliveryBranch.DELIVERED_WITHOUT_POD.value:
            # Ask for POD via inbound channel
            tool_calls.append(_send_to_driver("Thank you for confirming delivery. Please send the Proof of Delivery (POD) document."))
            actions_taken.append("Requested POD from driver")

            # Schedule POD follow-up timer
            from datetime import datetime as dt, timezone as tz
            fire_at = dt.now(tz.utc).isoformat()
            tool_calls.append({
                "tool": "create_timer",
                "arguments": {
                    "timer_type": "pod_followup",
                    "fire_at_utc": fire_at,
                    "reason": "Follow up on POD request",
                },
            })

            # Delivered without POD visibility per customer config
            delivered_visibility = customer_config.get("delivered_without_pod_visibility", "no_notification")
            escalation_channel = customer_config.get("escalation_channel", "email")
            if delivered_visibility == "notify_escalation_channel":
                if escalation_channel in ("email", "email_and_slack"):
                    tool_calls.append({"tool": "send_email", "arguments": {"recipient": "ops", "subject": "Delivery Confirmed Without POD", "body": "Driver confirmed delivery but POD is still pending."}})
                if escalation_channel in ("slack", "email_and_slack"):
                    tool_calls.append({"tool": "send_slack_message", "arguments": {"audience": "broker", "message": "Driver confirmed delivery but POD is still pending.", "escalation_type": "delivery_confirmed"}})

        elif branch == ConfirmDeliveryBranch.UNLOADING_STARTED.value:
            tool_calls.append(_send_to_driver("Thank you for the update. Please send POD when unloading is complete."))
            actions_taken.append("Acknowledged unloading started, requested POD")

        elif branch == ConfirmDeliveryBranch.OPERATIONAL_ISSUE.value:
            escalation_channel = customer_config.get("escalation_channel", "internal")
            issue_details = event_data.get("message", "Operational issue at delivery")
            for call in _escalate("operational", issue_details, escalation_channel):
                tool_calls.append(call)
            actions_taken.append(f"Escalated operational issue via {escalation_channel}")

        elif branch == ConfirmDeliveryBranch.BROKER_MESSAGES.value:
            tool_calls.append({
                "tool": "no_action",
                "arguments": {
                    "load_id": state.get("load_id"),
                    "event_id": state.get("event_id"),
                    "reason": "Broker message - no action per SOP",
                },
            })

        # Add semantic memory
        memory_operations.append({
            "operation": "add",
            "memory_type": "semantic",
            "scope": "load",
            "scope_id": state.get("load_id"),
            "content": f"Confirm delivery event {state.get('event_id')} classified as {branch}",
            "tags": [branch, "confirm_delivery"],
        })

        return {
            "tool_calls": tool_calls,
            "actions_taken": actions_taken,
            "memory_operations": memory_operations,
        }

    async def determine_state_transition(state: ConfirmDeliveryState) -> dict:
        """Determine if a state transition is needed."""
        branch = state.get("sop_branch", "")
        state_after = None
        pod_status = "pending"

        if branch == ConfirmDeliveryBranch.POD_DOCUMENT.value:
            pod_status = "collected"
            # POD collected - transition to pod_collected
            state_after = LoadState.POD_COLLECTED.value
        elif branch == ConfirmDeliveryBranch.DELIVERED_WITHOUT_POD.value:
            pod_status = "pending"
            state_after = LoadState.CONFIRM_DELIVERY.value

        return {
            "state_after": state_after,
            "pod_status": pod_status,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"State transition: {state_after or 'no change'}, POD status: {pod_status}")
            ],
        }

    # --- Routing Functions ---

    def route_after_classify(state: ConfirmDeliveryState) -> str:
        """Route after event classification."""
        branch = state.get("sop_branch", "")
        if branch in [ConfirmDeliveryBranch.NO_ACTION.value, ConfirmDeliveryBranch.BROKER_MESSAGES.value]:
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