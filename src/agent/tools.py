"""Agent tools for FreightHero Watchtower.

Implements the mock tools and memory tools that the agent
can use during workflow execution.

Tool contracts follow the specification in docs/wiki/tools.md:
- Communication: send_sms, send_email, forward_email, send_slack_message
- Attachment: check_attachment
- Load State: update_load_state, update_eta
- Timer: create_timer, cancel_timer, cancel_timers
- Human Work: create_task, create_issue
- Helper: get_load_info, validate_eta, get_appointment_time
- Internal: record_sop_branch, no_action, get_geofence_status
- Memory: memory_add, memory_retrieve, memory_update, memory_delete, memory_summarize, memory_filter
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from src.domain.enums import (
    AttachmentCategory,
    Channel,
    CustomerId,
    IssueType,
    MemoryOperation,
    MemoryScope,
    MemoryType,
    SenderType,
    SOPBranch,
    ConfirmDeliveryBranch,
)


# --- Communication Tools ---


@tool
def send_sms(recipient: str, message: str) -> dict:
    """Send an SMS-style message to the driver or dispatcher.

    Args:
        recipient: The recipient identifier (driver, dispatcher).
        message: Short text message content.

    Returns:
        Dictionary confirming the message was sent.
    """
    return {
        "ok": True,
        "channel": "sms",
        "message_id": f"sms-{uuid.uuid4()}",
        "recipient": recipient,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@tool
def send_email(recipient: str, subject: str, body: str) -> dict:
    """Send or reply to an operational email thread.

    Args:
        recipient: The recipient (driver, dispatcher, carrier_team, main_thread, or explicit email).
        subject: Email subject line.
        body: Email body text.

    Returns:
        Dictionary confirming the email was sent.
    """
    return {
        "ok": True,
        "channel": "email",
        "message_id": f"email-{uuid.uuid4()}",
        "recipient": recipient,
        "subject": subject,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@tool
def forward_email() -> dict:
    """Forward the current email and its attachments to the broker-provided special email address.

    Use this for forwarding documents as-is, not for composing an operational message.

    Returns:
        Dictionary confirming the email was forwarded.
    """
    return {
        "ok": True,
        "channel": "email",
        "message_id": f"fwd-{uuid.uuid4()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@tool
def send_slack_message(audience: str, message: str, escalation_type: str = "") -> dict:
    """Send internal or broker-visible Slack-style notification.

    Args:
        audience: The audience (internal, broker, customer).
        message: Notification message text.
        escalation_type: Optional escalation type string.

    Returns:
        Dictionary confirming the Slack message was sent.
    """
    return {
        "ok": True,
        "channel": "slack",
        "message_id": f"slack-{uuid.uuid4()}",
        "audience": audience,
        "escalation_type": escalation_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# --- Attachment Tool ---


@tool
def check_attachment(attachment_id: str) -> dict:
    """Classify one attachment using the fixture-provided metadata.

    Args:
        attachment_id: The attachment identifier to check.

    Returns:
        Dictionary with classification result including categories and description.
    """
    return {
        "ok": True,
        "attachment_id": attachment_id,
        "categories": ["other"],
        "description": "Attachment classification requires manual review",
    }


# --- Load State Tools ---


@tool
def update_load_state(target_state: str, reason: str) -> dict:
    """Update the load milestone state.

    Args:
        target_state: The new state (on_route_to_delivery, at_delivery, delivered, pod_collected).
        reason: Short text reason for the state transition.

    Returns:
        Dictionary confirming the state update.
    """
    return {
        "ok": True,
        "previous_state": "unknown",
        "new_state": target_state,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@tool
def update_eta(target_location: str, eta_utc: str, source: str = "driver") -> dict:
    """Store a driver-provided ETA.

    Args:
        target_location: The target location (delivery).
        eta_utc: ISO timestamp for the estimated arrival.
        source: Source of the ETA (driver, dispatcher, carrier, system).

    Returns:
        Dictionary confirming the ETA update.
    """
    return {
        "ok": True,
        "target_location": target_location,
        "eta_utc": eta_utc,
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# --- Timer Tools ---


@tool
def create_timer(timer_type: str, fire_at_utc: str, reason: str) -> dict:
    """Create a follow-up timer.

    Args:
        timer_type: Type of timer (eta_followup, pod_followup, delivery_status_followup, attachment_clarification).
        fire_at_utc: ISO timestamp when the timer should fire.
        reason: Short text reason for the timer.

    Returns:
        Dictionary confirming the timer creation.
    """
    return {
        "ok": True,
        "timer_id": f"timer-{uuid.uuid4()}",
        "timer_type": timer_type,
        "fire_at_utc": fire_at_utc,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@tool
def cancel_timer(timer_id: str) -> dict:
    """Cancel one timer by its ID.

    Args:
        timer_id: The timer identifier to cancel.

    Returns:
        Dictionary confirming the cancellation.
    """
    return {
        "ok": True,
        "timer_id": timer_id,
        "status": "cancelled",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@tool
def cancel_timers(timer_type: str = "") -> dict:
    """Cancel timers by type or all timers for the current load.

    Args:
        timer_type: Optional timer type to cancel. If empty, cancels all timers for the load.

    Returns:
        Dictionary confirming the cancellation.
    """
    return {
        "ok": True,
        "timer_type": timer_type,
        "status": "cancelled",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# --- Human Work Tools ---


@tool
def create_task(title: str, description: str, task_type: str) -> dict:
    """Create a non-urgent human follow-up task.

    Args:
        title: Short title for the task.
        description: Detailed description of the task.
        task_type: Type of task (missing_load_info, pod_review, lumper_review, manual_followup, other).

    Returns:
        Dictionary confirming the task creation.
    """
    return {
        "ok": True,
        "task_id": f"task-{uuid.uuid4()}",
        "title": title,
        "description": description,
        "task_type": task_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@tool
def create_issue(title: str, description: str, issue_type: str) -> dict:
    """Create an urgent operational issue.

    Args:
        title: Short title for the issue.
        description: Detailed description of the issue.
        issue_type: Type of issue (equipment_failure, delivery_delay, facility_problem, other).

    Returns:
        Dictionary confirming the issue creation.
    """
    return {
        "ok": True,
        "issue_id": f"issue-{uuid.uuid4()}",
        "title": title,
        "description": description,
        "issue_type": issue_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# --- Helper Tools ---


@tool
def get_load_info(field: str) -> dict:
    """Read a specific field or section from the persisted load data.

    Args:
        field: Short string such as delivery_address, receiver_phone, delivery_reference, or driver_contact.

    Returns:
        Dictionary with the field value, or error if missing.
    """
    return {
        "ok": True,
        "field": field,
        "value": f"Retrieved {field}",
    }


@tool
def validate_eta(raw_eta: str, delivery_timezone: str) -> dict:
    """Validate and normalize a driver-provided ETA against the delivery appointment and timezone.

    Args:
        raw_eta: Text from the inbound message (e.g., "3pm", "14:30").
        delivery_timezone: IANA timezone string (e.g., America/Chicago).

    Returns:
        Dictionary with validated ETA and plausibility flag.
    """
    return {
        "ok": True,
        "eta_utc": "2026-05-11T19:30:00Z",
        "is_plausible": True,
    }


@tool
def get_appointment_time(stop_type: str) -> dict:
    """Return the appointment time for a stop.

    Args:
        stop_type: Type of stop (pickup or delivery).

    Returns:
        Dictionary with appointment details.
    """
    return {
        "ok": True,
        "stop_type": stop_type,
        "appointment": {
            "type": "fixed",
            "start_utc": "2026-05-11T20:00:00Z",
            "timezone": "America/Chicago",
        },
    }


# --- Internal Tools ---


@tool
def record_sop_branch(
    load_id: str,
    event_id: str,
    branch: str,
    reason: str,
) -> dict:
    """Record which SOP branch was taken and why.

    Args:
        load_id: The load identifier.
        event_id: The event identifier.
        branch: The SOP branch that was selected.
        reason: The reason for selecting this branch.

    Returns:
        Dictionary confirming the branch recording.
    """
    return {
        "record_id": f"branch-{uuid.uuid4()}",
        "load_id": load_id,
        "event_id": event_id,
        "branch": branch,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@tool
def no_action(load_id: str, event_id: str, reason: str) -> dict:
    """Record that no action was taken for an event.

    Args:
        load_id: The load identifier.
        event_id: The event identifier.
        reason: The reason for taking no action.

    Returns:
        Dictionary confirming the no-action recording.
    """
    return {
        "record_id": f"noaction-{uuid.uuid4()}",
        "load_id": load_id,
        "event_id": event_id,
        "action": "none",
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@tool
def get_geofence_status(load_id: str, latitude: float, longitude: float) -> dict:
    """Check if coordinates are within the delivery geofence.

    Args:
        load_id: The load identifier.
        latitude: Driver's latitude.
        longitude: Driver's longitude.

    Returns:
        Dictionary with geofence status.
    """
    return {
        "load_id": load_id,
        "latitude": latitude,
        "longitude": longitude,
        "within_geofence": False,
        "distance_miles": 999,
        "geofence_radius_miles": 1,
    }


# --- Memory Tools (6) ---


@tool
def memory_add(
    memory_type: str,
    scope: str,
    scope_id: str,
    content: str,
    tags: str = "",
    confidence: float = 1.0,
    content_type: str = "fact",
) -> dict:
    """Add a new memory entry to the agent's memory system.

    Args:
        memory_type: Type of memory (episodic, semantic, procedural).
        scope: Scope of the memory (load, customer, global).
        scope_id: Identifier within the scope (e.g., load ID or customer ID).
        content: The memory content to store.
        tags: Comma-separated tags for categorization.
        confidence: Confidence score (0-1).
        content_type: Type of content (fact, summary, procedure).

    Returns:
        Dictionary with memory_id and status.
    """
    return {
        "memory_id": f"mem-{uuid.uuid4()}",
        "memory_type": memory_type,
        "scope": scope,
        "scope_id": scope_id,
        "status": "added",
    }


@tool
def memory_retrieve(
    scope: str,
    scope_id: str,
    memory_type: str = "",
    tags: str = "",
    limit: int = 10,
) -> dict:
    """Retrieve memories matching the given criteria.

    Args:
        scope: Memory scope to search (load, customer, global).
        scope_id: Identifier within the scope.
        memory_type: Optional filter by memory type.
        tags: Optional comma-separated tags to filter by.
        limit: Maximum number of results.

    Returns:
        Dictionary with list of matching memories.
    """
    return {
        "memories": [],
        "count": 0,
        "scope": scope,
        "scope_id": scope_id,
    }


@tool
def memory_update(
    memory_id: str,
    content: str = "",
    tags: str = "",
    confidence: float = -1,
) -> dict:
    """Update an existing memory entry.

    Args:
        memory_id: The memory identifier to update.
        content: New content (optional).
        tags: New comma-separated tags (optional).
        confidence: New confidence score (optional, -1 to skip).

    Returns:
        Dictionary with update status.
    """
    return {
        "memory_id": memory_id,
        "status": "updated",
    }


@tool
def memory_delete(memory_id: str) -> dict:
    """Delete a memory entry.

    Args:
        memory_id: The memory identifier to delete.

    Returns:
        Dictionary with deletion status.
    """
    return {
        "memory_id": memory_id,
        "status": "deleted",
    }


@tool
def memory_summarize(
    scope: str,
    scope_id: str,
    memory_type: str,
) -> dict:
    """Summarize memories of a given type and scope.

    Creates a compressed summary and archives the original memories.

    Args:
        scope: Memory scope.
        scope_id: Identifier within the scope.
        memory_type: Type of memories to summarize.

    Returns:
        Dictionary with summary_id and status.
    """
    return {
        "summary_id": f"summary-{uuid.uuid4()}",
        "scope": scope,
        "scope_id": scope_id,
        "memory_type": memory_type,
        "status": "summarized",
    }


@tool
def memory_filter(
    scope: str,
    scope_id: str,
    memory_type: str,
    relevance_threshold: float = 0.5,
) -> dict:
    """Filter out low-relevance memories.

    Removes memories below the relevance threshold.

    Args:
        scope: Memory scope.
        scope_id: Identifier within the scope.
        memory_type: Type of memories to filter.
        relevance_threshold: Minimum relevance score to keep (0-1).

    Returns:
        Dictionary with count of removed memories.
    """
    return {
        "removed_count": 0,
        "scope": scope,
        "scope_id": scope_id,
        "memory_type": memory_type,
        "status": "filtered",
    }


# --- Tool Registry ---

ALL_TOOLS = [
    # Communication tools
    send_sms,
    send_email,
    forward_email,
    send_slack_message,
    # Attachment tools
    check_attachment,
    # Load state tools
    update_load_state,
    update_eta,
    # Timer tools
    create_timer,
    cancel_timer,
    cancel_timers,
    # Human work tools
    create_task,
    create_issue,
    # Helper tools
    get_load_info,
    validate_eta,
    get_appointment_time,
    # Internal tools
    record_sop_branch,
    no_action,
    get_geofence_status,
    # Memory tools
    memory_add,
    memory_retrieve,
    memory_update,
    memory_delete,
    memory_summarize,
    memory_filter,
]

COMMUNICATION_TOOLS = [
    send_sms,
    send_email,
    forward_email,
    send_slack_message,
]

MOCK_TOOLS = [
    # Communication tools
    send_sms,
    send_email,
    forward_email,
    send_slack_message,
    # Attachment tools
    check_attachment,
    # Load state tools
    update_load_state,
    update_eta,
    # Timer tools
    create_timer,
    cancel_timer,
    cancel_timers,
    # Human work tools
    create_task,
    create_issue,
    # Helper tools
    get_load_info,
    validate_eta,
    get_appointment_time,
    # Internal tools
    record_sop_branch,
    no_action,
    get_geofence_status,
]

MEMORY_TOOLS = [
    memory_add,
    memory_retrieve,
    memory_update,
    memory_delete,
    memory_summarize,
    memory_filter,
]
