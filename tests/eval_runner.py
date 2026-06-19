#!/usr/bin/env python3
"""Eval runner for FreightHero Watchtower.

Loads test cases from docs/specs/test-cases.json, executes them against
the agent workflows, and validates required_tool_calls, forbidden_tool_calls,
and expected_state.

Usage:
    python -m tests.eval_runner
    python -m tests.eval_runner --case 3b_load_question_found
    python -m tests.eval_runner --verbose
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.eta_checkpoint import create_eta_checkpoint_workflow, ETACheckpointState
from src.agent.confirm_delivery import create_confirm_delivery_workflow, ConfirmDeliveryState
from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    SOPBranch,
    ConfirmDeliveryBranch,
    SenderType,
    Channel,
)


# --- Customer Configurations ---

CUSTOMER_CONFIGS = {
    "customer_a": {
        "customer_id": "customer_a",
        "escalation_channel": "email",
        "missing_load_info_action": "create_task",
        "pod_validation_type": "automatic",
        "pod_received_visibility": "escalation_channel",
        "delivered_without_pod_visibility": "escalation_channel",
        "delivery_geofence_radius_miles": 1,
        "eta_followup_timer_minutes": 30,
        "lumper_receipt_handling": "classify_and_review_task",
        "first_arrival_message": "ask_unloading_status_and_pod",
    },
    "customer_b": {
        "customer_id": "customer_b",
        "escalation_channel": "slack",
        "missing_load_info_action": "create_task_and_send_visibility",
        "pod_validation_type": "human_review",
        "pod_received_visibility": "none",
        "delivered_without_pod_visibility": "none",
        "delivery_geofence_radius_miles": 2,
        "eta_followup_timer_minutes": 60,
        "lumper_receipt_handling": "classify_and_review_task",
        "first_arrival_message": "confirm_unloading_start_and_send_pod",
    },
    "customer_c": {
        "customer_id": "customer_c",
        "escalation_channel": "both",
        "missing_load_info_action": "create_task",
        "pod_validation_type": "automatic",
        "pod_received_visibility": "none",
        "delivered_without_pod_visibility": "escalation_channel",
        "delivery_geofence_radius_miles": 3,
        "eta_followup_timer_minutes": 45,
        "lumper_receipt_handling": "forward_email_if_lumper_else_review_task",
        "first_arrival_message": "ask_unloading_pod_and_lumper",
    },
}


# --- Tool Name Mapping ---
# Maps spec tool names to implementation tool names.
# After the tools.py refactor, implementation names now match spec names exactly.
# This map is kept for backward compatibility and to handle any remaining aliases.

TOOL_NAME_MAP = {
    # Communication tools - now match spec exactly
    "send_sms": "send_sms",
    "send_email": "send_email",
    "forward_email": "forward_email",
    "send_slack_message": "send_slack_message",
    # Attachment tools
    "check_attachment": "check_attachment",
    "classify_attachment": "check_attachment",  # legacy alias
    # Load state tools
    "update_load_state": "update_load_state",
    "update_eta": "update_eta",
    # Timer tools
    "create_timer": "create_timer",
    "cancel_timer": "cancel_timer",
    "cancel_timers": "cancel_timers",
    # Human work tools
    "create_task": "create_task",
    "create_issue": "create_issue",
    # Helper tools
    "get_load_info": "get_load_info",
    "validate_eta": "validate_eta",
    "get_appointment_time": "get_appointment_time",
    # Internal tools
    "record_sop_branch": "record_sop_branch",
    "no_action": "no_action",
    "get_geofence_status": "get_geofence_status",
    # Legacy aliases from old implementation
    "send_message": "send_sms",  # old generic tool maps to send_sms for backward compat
    "escalate_to_ops": "create_issue",  # old tool maps to create_issue
    "schedule_followup": "create_timer",  # old tool maps to create_timer
    "cancel_followup": "cancel_timer",  # old tool maps to cancel_timer
}

# Channel mapping for forbidden tool checks
# Maps spec tool names to the channel they use
CHANNEL_MAP = {
    "send_sms": "sms",
    "send_email": "email",
    "forward_email": "email",
    "send_slack_message": "slack",
}


def normalize_tool_name(tool_name: str) -> str:
    """Normalize tool names between spec and implementation."""
    return TOOL_NAME_MAP.get(tool_name, tool_name)


# --- Load Data Builder ---

def build_load_data(base_load: dict, patch: dict | None = None) -> dict:
    """Build load data from base_load spec, applying optional patches."""
    load_data = dict(base_load.get("load_data", {}))

    if patch:
        for key, value in patch.items():
            # Handle nested patch keys like "stops[1].reference_numbers.receiver_phone"
            parts = key.replace("[", ".").replace("]", "").split(".")
            current = load_data
            for part in parts[:-1]:
                if part.isdigit():
                    current = current[int(part)]
                else:
                    current = current.setdefault(part, {})
            last = parts[-1]
            if last.isdigit():
                current[int(last)] = value
            else:
                current[last] = value

    return load_data


# --- Event Builder ---

def build_event_state(case: dict, base_load: dict) -> dict:
    """Build the initial workflow state from a test case event."""
    events = case.get("events", [])
    first_event = events[0] if events else {}

    event_type_raw = first_event.get("event_type", "")
    customer_id = case.get("customer_id", first_event.get("customer_id", "customer_a"))
    initial_state = case.get("initial_state", "on_route_to_delivery")
    load_data_patch = case.get("load_data_patch")
    load_data = build_load_data(base_load, load_data_patch)

    # Map event type
    if event_type_raw == "tracking":
        event_type = EventType.TRACKING.value
        tracking = first_event.get("tracking", {})
        event_data = {
            "latitude": tracking.get("lat", 0),
            "longitude": tracking.get("lng", 0),
            "distance_to_delivery": tracking.get("distance_to_delivery_miles", 999),
            "ping_sequence": tracking.get("ping_sequence", 1),
            "provider": tracking.get("provider", "mock"),
        }
    elif event_type_raw == "inbound_communication":
        event_type = EventType.INBOUND_COMMUNICATION.value
        comm = first_event.get("inbound_communication", {})
        event_data = {
            "sender_type": comm.get("sender_type", "driver"),
            "channel": comm.get("channel", "sms"),
            "message": comm.get("content", ""),
            "sender_name": comm.get("sender_name", ""),
            "attachments": comm.get("attachments", []),
        }
    elif event_type_raw == "load_update":
        event_type = EventType.LOAD_UPDATE.value
        event_data = first_event.get("load_update", {})
    else:
        event_type = event_type_raw
        event_data = first_event.get("event_data", {})

    customer_config = CUSTOMER_CONFIGS.get(customer_id, CUSTOMER_CONFIGS["customer_a"])

    return {
        "event_id": first_event.get("event_id", f"evt-{uuid.uuid4()}"),
        "load_id": first_event.get("load_id", base_load.get("load_id", "load-visible-001")),
        "customer_id": customer_id,
        "event_type": event_type,
        "event_data": event_data,
        "load_data": load_data,
        "current_state": initial_state,
        "current_eta_utc": "2026-05-11T19:30:00Z",
        "customer_config": customer_config,
        "sop_content": "",
        "messages": [],
        "tool_calls": [],
        "memory_operations": [],
        "actions_taken": [],
    }


# --- Assertion Engine ---

class EvalResult:
    """Result of evaluating a single test case."""

    def __init__(self, case_id: str, title: str):
        self.case_id = case_id
        self.title = title
        self.passed = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.tool_calls: list[dict] = []
        self.sop_branch: str = ""
        self.state_after: str | None = None

    def add_error(self, msg: str):
        self.passed = False
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"[{status}] {self.case_id}: {self.title}"


def assert_required_tool_calls(result: EvalResult, tool_calls: list[dict], required: list[dict]):
    """Assert that all required tool calls are present in the actual tool calls."""
    for req in required:
        tool_name = req.get("tool", "")
        normalized = normalize_tool_name(tool_name)

        # Find matching tool calls
        matches = [
            tc for tc in tool_calls
            if tc.get("tool") == normalized or tc.get("tool") == tool_name
        ]

        if not matches:
            result.add_error(
                f"Required tool call missing: {tool_name} (normalized: {normalized}). "
                f"Actual tools: {[tc.get('tool') for tc in tool_calls]}"
            )
            continue

        # Check "contains" constraint
        if "contains" in req:
            contains_text = req["contains"]
            found = any(
                contains_text.lower() in json.dumps(tc.get("arguments", {})).lower()
                for tc in matches
            )
            if not found:
                result.add_error(
                    f"Required tool call {tool_name} with content containing '{contains_text}' not found. "
                    f"Actual arguments: {[tc.get('arguments') for tc in matches]}"
                )

        # Check "arguments" constraint
        if "arguments" in req:
            for key, value in req["arguments"].items():
                # Spec argument names now match implementation argument names exactly
                found = any(
                    tc.get("arguments", {}).get(key) == value
                    for tc in matches
                )
                if not found:
                    result.add_warning(
                        f"Tool {tool_name}: expected argument {key}={value} not found in any call. "
                        f"Actual: {[tc.get('arguments') for tc in matches]}"
                    )


def assert_forbidden_tool_calls(result: EvalResult, tool_calls: list[dict], forbidden: list[str]):
    """Assert that none of the forbidden tool calls are present.
    
    Now that tool names match the spec exactly, we can do direct name matching.
    Communication tools (send_sms, send_email, etc.) are separate tools,
    so we match by exact tool name.
    """
    for tool_name in forbidden:
        normalized = normalize_tool_name(tool_name)
        
        # Direct name matching - tools now match spec names exactly
        matches = [
            tc for tc in tool_calls
            if tc.get("tool") == normalized or tc.get("tool") == tool_name
        ]
        
        if matches:
            result.add_error(
                f"Forbidden tool call found: {tool_name} (normalized: {normalized}). "
                f"Matching calls: {len(matches)}"
            )


def assert_expected_state(result: EvalResult, actual_state: str | None, expected_state: str):
    """Assert that the final state matches the expected state."""
    if actual_state is None and expected_state != "on_route_to_delivery":
        # No state transition happened, check if that's expected
        result.add_warning(
            f"No state transition occurred. Expected: {expected_state}"
        )
    elif actual_state and actual_state != expected_state:
        result.add_error(
            f"Expected state: {expected_state}, actual: {actual_state}"
        )


# --- Workflow Execution ---

async def run_workflow(state: dict, initial_state: str) -> dict:
    """Run the appropriate workflow based on initial state and event type."""
    # If the event has attachments (POD, lumper, etc.), use confirm delivery workflow
    event_data = state.get("event_data", {})
    attachments = event_data.get("attachments", [])
    has_pod_or_delivery_attachment = False
    if attachments:
        for att in attachments:
            mock_cats = att.get("mock_classification", {}).get("categories", [])
            att_class = att.get("classification", "").lower()
            if any(c in ["document_pod", "proof_of_delivery"] for c in mock_cats) or att_class in ["pod", "proof_of_delivery"]:
                has_pod_or_delivery_attachment = True
                break

    # Also check if the message indicates delivery confirmation
    message = event_data.get("message", "").lower()
    delivery_keywords = ["pod", "proof of delivery", "delivery receipt", "unloaded", "empty", "delivered"]
    is_delivery_confirmation = any(kw in message for kw in delivery_keywords)

    if initial_state in ("on_route_to_delivery",) and not has_pod_or_delivery_attachment and not is_delivery_confirmation:
        workflow = create_eta_checkpoint_workflow()
    else:
        workflow = create_confirm_delivery_workflow()

    config = {"configurable": {"thread_id": f"eval-{uuid.uuid4()}"}}
    result = await workflow.ainvoke(state, config)
    return result


# --- Multi-event Processing ---

async def run_multi_event_workflow(case: dict, base_load: dict) -> dict:
    """Process multiple events in sequence (e.g., 3 tracking pings)."""
    events = case.get("events", [])
    initial_state = case.get("initial_state", "on_route_to_delivery")
    customer_id = case.get("customer_id", "customer_a")
    load_data_patch = case.get("load_data_patch")
    load_data = build_load_data(base_load, load_data_patch)
    customer_config = CUSTOMER_CONFIGS.get(customer_id, CUSTOMER_CONFIGS["customer_a"])

    all_tool_calls = []
    final_state = initial_state
    sop_branch = ""
    state_after = None

    for event in events:
        event_type_raw = event.get("event_type", "")

        if event_type_raw == "tracking":
            event_type = EventType.TRACKING.value
            tracking = event.get("tracking", {})
            event_data = {
                "latitude": tracking.get("lat", 0),
                "longitude": tracking.get("lng", 0),
                "distance_to_delivery": tracking.get("distance_to_delivery_miles", 999),
                "ping_sequence": tracking.get("ping_sequence", 1),
                "provider": tracking.get("provider", "mock"),
            }
        elif event_type_raw == "inbound_communication":
            event_type = EventType.INBOUND_COMMUNICATION.value
            comm = event.get("inbound_communication", {})
            event_data = {
                "sender_type": comm.get("sender_type", "driver"),
                "channel": comm.get("channel", "sms"),
                "message": comm.get("content", ""),
                "sender_name": comm.get("sender_name", ""),
                "attachments": comm.get("attachments", []),
            }
        else:
            event_type = event_type_raw
            event_data = event.get("event_data", {})

        state = {
            "event_id": event.get("event_id", f"evt-{uuid.uuid4()}"),
            "load_id": event.get("load_id", base_load.get("load_id", "load-visible-001")),
            "customer_id": customer_id,
            "event_type": event_type,
            "event_data": event_data,
            "load_data": load_data,
            "current_state": final_state,
            "current_eta_utc": "2026-05-11T19:30:00Z",
            "customer_config": customer_config,
            "sop_content": "",
            "messages": [],
            "tool_calls": [],
            "memory_operations": [],
            "actions_taken": [],
        }

        result = await run_workflow(state, final_state)
        all_tool_calls.extend(result.get("tool_calls", []))
        sop_branch = result.get("sop_branch", "")
        state_after = result.get("state_after")
        if state_after:
            final_state = state_after

    return {
        "tool_calls": all_tool_calls,
        "sop_branch": sop_branch,
        "state_after": state_after,
        "final_state": final_state,
    }


# --- Main Eval Runner ---

async def run_eval(
    test_cases_path: Path | None = None,
    case_filter: str | None = None,
    verbose: bool = False,
) -> list[EvalResult]:
    """Run all test cases and return results."""
    if test_cases_path is None:
        test_cases_path = PROJECT_ROOT / "docs" / "specs" / "test-cases.json"

    with open(test_cases_path) as f:
        spec = json.load(f)

    base_load = spec.get("base_load", {})
    cases = spec.get("cases", [])

    results: list[EvalResult] = []

    for case in cases:
        case_id = case.get("id", "unknown")
        title = case.get("title", "Untitled")

        # Filter by case ID if specified
        if case_filter and case_filter not in case_id:
            continue

        result = EvalResult(case_id=case_id, title=title)

        try:
            events = case.get("events", [])
            expected = case.get("expected", {})
            required_tool_calls = expected.get("required_tool_calls", [])
            forbidden_tool_calls = expected.get("forbidden_tool_calls", [])
            expected_state = expected.get("expected_state", "")

            if len(events) > 1:
                # Multi-event case (e.g., 3 tracking pings)
                workflow_result = await run_multi_event_workflow(case, base_load)
            else:
                # Single event case
                state = build_event_state(case, base_load)
                initial_state = case.get("initial_state", "on_route_to_delivery")
                workflow_result = await run_workflow(state, initial_state)

            result.tool_calls = workflow_result.get("tool_calls", [])
            result.sop_branch = workflow_result.get("sop_branch", "")
            result.state_after = workflow_result.get("state_after") or workflow_result.get("final_state")

            # Assert required tool calls
            assert_required_tool_calls(result, result.tool_calls, required_tool_calls)

            # Assert forbidden tool calls
            assert_forbidden_tool_calls(result, result.tool_calls, forbidden_tool_calls)

            # Assert expected state
            if expected_state:
                assert_expected_state(result, result.state_after, expected_state)

        except Exception as e:
            result.add_error(f"Exception during execution: {e}")

        results.append(result)

        if verbose or not result.passed:
            print(result)
            if result.errors:
                for err in result.errors:
                    print(f"  ❌ {err}")
            if result.warnings:
                for warn in result.warnings:
                    print(f"  ⚠️  {warn}")
            if verbose and result.tool_calls:
                print(f"  Tool calls: {[tc.get('tool') for tc in result.tool_calls]}")
                print(f"  SOP branch: {result.sop_branch}")
                print(f"  State after: {result.state_after}")
        else:
            print(result)

    return results


def print_summary(results: list[EvalResult]):
    """Print a summary of eval results."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    print("\n" + "=" * 60)
    print(f"EVAL SUMMARY: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        print("\nFailed cases:")
        for r in results:
            if not r.passed:
                print(f"  ❌ {r.case_id}: {r.title}")
                for err in r.errors:
                    print(f"     {err}")

    return failed == 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="FreightHero Eval Runner")
    parser.add_argument("--case", type=str, help="Run specific case by ID substring")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--test-cases",
        type=str,
        help="Path to test-cases.json",
    )
    args = parser.parse_args()

    test_cases_path = Path(args.test_cases) if args.test_cases else None

    results = asyncio.run(run_eval(
        test_cases_path=test_cases_path,
        case_filter=args.case,
        verbose=args.verbose,
    ))

    all_passed = print_summary(results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()