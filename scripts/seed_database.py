#!/usr/bin/env python3
"""
Database Seed Script for FreightHero Watchtower

This script populates the database with realistic demo data for demonstration purposes.
It creates:
- 3 loads (one per customer type: A, B, C)
- Sample events for each SOP branch
- Pre-populated agent runs and tool calls
- Memory entries for demonstration

Usage:
    python scripts/seed_database.py

Or with virtual environment:
    source .venv/bin/activate && python scripts/seed_database.py
"""

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import List

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    SenderType,
    Channel,
    AttachmentCategory,
    MemoryType,
    MemoryScope,
    MemoryOperation,
    TaskType,
    IssueType,
    TimerType,
)
from src.domain.value_objects import (
    Address,
    Coordinates,
    Appointment,
    PersonContact,
    Company,
    Stop,
    Attachment,
    AttachmentClassification,
    InboundCommunication,
)
from src.domain.models import Load, Event, AgentRun, ToolCall, MemoryOperationLog
from src.infrastructure.database import DatabaseManager, Base
from src.infrastructure.repositories import (
    get_load_repository,
    get_event_repository,
    get_agent_run_repository,
    get_tool_call_repository,
    get_memory_repository,
)
from sqlalchemy.ext.asyncio import AsyncSession


# Sample data for realistic demo
SAMPLE_LOADS = [
    {
        "load_id": "load-customer-a-001",
        "customer_id": CustomerId.CUSTOMER_A,
        "external_load_id": "FH-2026-001",
        "po_number": "PO-7788-A",
        "instructions": "Receiver requires check-in at guard shack. Follow BOL temperature instructions.",
        "current_state": LoadState.AT_DELIVERY,
        "current_eta_utc": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "companies": {
            "broker": Company(name="Example Broker", uuid="broker-example"),
            "shipper": Company(name="Example Shipper", uuid="shipper-example"),
            "carrier": Company(name="Example Carrier", uuid="carrier-example"),
        },
        "contacts": {
            "driver": PersonContact(first_name="Sam", last_name="Driver", phone="+15555550100", uuid="driver-sam"),
            "dispatcher": PersonContact(first_name="Dana", last_name="Dispatch", email="dispatch@example.com", uuid="dispatcher-dana"),
            "broker": PersonContact(first_name="Blake", last_name="Broker", email="broker@example.com", uuid="broker-contact"),
        },
        "stops": [
            Stop(
                stop_id="pickup-1",
                type="pickup",
                status="departed",
                address=Address(line_1="123 Pickup Ave", city="Chicago", state="IL", postal_code="60601", country="US"),
                appointment=Appointment(type="fixed", start_utc=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), timezone="America/Chicago"),
                coordinates=Coordinates(lat=41.8781, lng=-87.6298),
                reference_numbers={"pickup": "PU-123"},
            ),
            Stop(
                stop_id="delivery-1",
                type="delivery",
                status="en_route",
                address=Address(line_1="456 Delivery St", line_2="Dock 4", city="Dallas", state="TX", postal_code="75201", country="US"),
                appointment=Appointment(type="fixed", start_utc=(datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(), timezone="America/Chicago"),
                coordinates=Coordinates(lat=32.7767, lng=-96.7970),
                reference_numbers={"delivery": "DEL-456", "receiver_phone": "+15555550200"},
            ),
        ],
    },
    {
        "load_id": "load-customer-b-002",
        "customer_id": CustomerId.CUSTOMER_B,
        "external_load_id": "FH-2026-002",
        "po_number": "PO-9900-B",
        "instructions": "Customer B requires human POD review. Use Slack for escalations.",
        "current_state": LoadState.ON_ROUTE_TO_DELIVERY,
        "current_eta_utc": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
        "companies": {
            "broker": Company(name="Premium Broker", uuid="broker-premium"),
            "shipper": Company(name="Premium Shipper", uuid="shipper-premium"),
            "carrier": Company(name="Premium Carrier", uuid="carrier-premium"),
        },
        "contacts": {
            "driver": PersonContact(first_name="Maria", last_name="Rodriguez", phone="+15555550200", uuid="driver-maria"),
            "dispatcher": PersonContact(first_name="Carlos", last_name="Dispatch", email="carlos@premium.com", uuid="dispatcher-carlos"),
            "broker": PersonContact(first_name="Brian", last_name="Premium", email="brian@premium.com", uuid="broker-premium"),
        },
        "stops": [
            Stop(
                stop_id="pickup-2",
                type="pickup",
                status="departed",
                address=Address(line_1="789 Industrial Blvd", city="Houston", state="TX", postal_code="77001", country="US"),
                appointment=Appointment(type="fixed", start_utc=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), timezone="America/Chicago"),
                coordinates=Coordinates(lat=29.7604, lng=-95.3698),
                reference_numbers={"pickup": "PU-789"},
            ),
            Stop(
                stop_id="delivery-2",
                type="delivery",
                status="en_route",
                address=Address(line_1="321 Commerce Way", line_2="Bay 7", city="Atlanta", state="GA", postal_code="30301", country="US"),
                appointment=Appointment(type="fixed", start_utc=(datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(), timezone="America/New_York"),
                coordinates=Coordinates(lat=33.7490, lng=-84.3880),
                reference_numbers={"delivery": "DEL-321"},
            ),
        ],
    },
    {
        "load_id": "load-customer-c-003",
        "customer_id": CustomerId.CUSTOMER_C,
        "external_load_id": "FH-2026-003",
        "po_number": "PO-5544-C",
        "instructions": "Customer C: Forward lumper receipts via email. Dual escalation (email + Slack).",
        "current_state": LoadState.POD_COLLECTED,
        "current_eta_utc": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "companies": {
            "broker": Company(name="Elite Broker", uuid="broker-elite"),
            "shipper": Company(name="Elite Shipper", uuid="shipper-elite"),
            "carrier": Company(name="Elite Carrier", uuid="carrier-elite"),
        },
        "contacts": {
            "driver": PersonContact(first_name="James", last_name="Wilson", phone="+15555550300", uuid="driver-james"),
            "dispatcher": PersonContact(first_name="Jennifer", last_name="Dispatch", email="jen@elite.com", uuid="dispatcher-jen"),
            "broker": PersonContact(first_name="Beth", last_name="Elite", email="beth@elite.com", uuid="broker-elite"),
        },
        "stops": [
            Stop(
                stop_id="pickup-3",
                type="pickup",
                status="departed",
                address=Address(line_1="555 Warehouse Dr", city="Phoenix", state="AZ", postal_code="85001", country="US"),
                appointment=Appointment(type="fixed", start_utc=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), timezone="America/Phoenix"),
                coordinates=Coordinates(lat=33.4484, lng=-112.0740),
                reference_numbers={"pickup": "PU-555"},
            ),
            Stop(
                stop_id="delivery-3",
                type="delivery",
                status="delivered",
                address=Address(line_1="888 Distribution Center", line_2="Door 12", city="Las Vegas", state="NV", postal_code="89101", country="US"),
                appointment=Appointment(type="fixed", start_utc=(datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(), timezone="America/Los_Angeles"),
                coordinates=Coordinates(lat=36.1699, lng=-115.1398),
                reference_numbers={"delivery": "DEL-888"},
            ),
        ],
    },
]


async def seed_loads(session: AsyncSession) -> List[Load]:
    """Seed sample loads into the database."""
    load_repo = get_load_repository(session)
    created_loads = []

    for load_data in SAMPLE_LOADS:
        load = Load(**load_data)
        await load_repo.save(load)
        created_loads.append(load)
        print(f"✅ Created load: {load.load_id} ({load.customer_id.value}) - State: {load.current_state.value}")

    return created_loads


async def seed_events(session: AsyncSession, loads: List[Load]) -> List[Event]:
    """Seed sample events for each load."""
    event_repo = get_event_repository(session)
    created_events = []

    # Events for Customer A load (at_delivery state)
    events_a = [
        Event(
            event_id=f"evt-a-{uuid.uuid4()}",
            event_type=EventType.INBOUND_COMMUNICATION,
            load_id=loads[0].load_id,
            customer_id=CustomerId.CUSTOMER_A,
            occurred_at=(datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
            event_data=InboundCommunication(
                channel=Channel.SMS,
                sender_type=SenderType.DRIVER,
                sender_name="Sam Driver",
                content="I've arrived at the delivery location.",
                attachments=[],
            ).model_dump(),
        ),
        Event(
            event_id=f"evt-a-{uuid.uuid4()}",
            event_type=EventType.INBOUND_COMMUNICATION,
            load_id=loads[0].load_id,
            customer_id=CustomerId.CUSTOMER_A,
            occurred_at=(datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            event_data=InboundCommunication(
                channel=Channel.SMS,
                sender_type=SenderType.DRIVER,
                sender_name="Sam Driver",
                content="Unloading has started. Will send POD when done.",
                attachments=[],
            ).model_dump(),
        ),
    ]

    # Events for Customer B load (on_route_to_delivery state)
    events_b = [
        Event(
            event_id=f"evt-b-{uuid.uuid4()}",
            event_type=EventType.INBOUND_COMMUNICATION,
            load_id=loads[1].load_id,
            customer_id=CustomerId.CUSTOMER_B,
            occurred_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            event_data=InboundCommunication(
                channel=Channel.SMS,
                sender_type=SenderType.DRIVER,
                sender_name="Maria Rodriguez",
                content="What's the delivery appointment time?",
                attachments=[],
            ).model_dump(),
        ),
        Event(
            event_id=f"evt-b-{uuid.uuid4()}",
            event_type=EventType.TRACKING,
            load_id=loads[1].load_id,
            customer_id=CustomerId.CUSTOMER_B,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            event_data={
                "latitude": 33.5,
                "longitude": -84.2,
                "distance_to_delivery": 15.3,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ),
    ]

    # Events for Customer C load (pod_collected state)
    pod_attachment = Attachment(
        attachment_id=f"att-{uuid.uuid4()}",
        file_name="pod_signed.pdf",
        mime_type="application/pdf",
        mock_classification=AttachmentClassification(
            categories=[AttachmentCategory.DOCUMENT_POD],
            description="Proof of Delivery document with signature",
        ),
    )

    events_c = [
        Event(
            event_id=f"evt-c-{uuid.uuid4()}",
            event_type=EventType.INBOUND_COMMUNICATION,
            load_id=loads[2].load_id,
            customer_id=CustomerId.CUSTOMER_C,
            occurred_at=(datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
            event_data=InboundCommunication(
                channel=Channel.EMAIL,
                sender_type=SenderType.DRIVER,
                sender_name="James Wilson",
                content="Delivery complete. POD attached.",
                attachments=[pod_attachment.model_dump()],
            ).model_dump(),
        ),
    ]

    all_events = events_a + events_b + events_c
    for event in all_events:
        await event_repo.save(event)
        created_events.append(event)
        print(f"✅ Created event: {event.event_id} ({event.event_type.value}) for load {event.load_id}")

    return created_events


async def seed_agent_runs(session: AsyncSession, loads: List[Load], events: List[Event]) -> List[AgentRun]:
    """Seed sample agent runs."""
    agent_run_repo = get_agent_run_repository(session)
    created_runs = []

    for i, load in enumerate(loads):
        load_events = [e for e in events if e.load_id == load.load_id]
        for event in load_events:
            agent_run = AgentRun(
                run_id=str(uuid.uuid4()),
                load_id=load.load_id,
                customer_id=load.customer_id,
                event_id=event.event_id,
                workflow="delivery_eta_checkpoint" if load.current_state in [LoadState.ON_ROUTE_TO_DELIVERY, LoadState.AT_DELIVERY] else "confirm_delivery",
                status="completed",
                started_at=datetime.now(timezone.utc) - timedelta(hours=2),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=1),
                tool_calls=[],
                memory_operations=[],
                sop_branch="tracking_ping" if i == 0 else "load_information_question",
                customer_rules_applied=[],
                branch_reason="Demo agent run for seed data",
            )
            await agent_run_repo.save(agent_run)
            created_runs.append(agent_run)
            print(f"✅ Created agent run: {agent_run.run_id} for load {load.load_id}")

    return created_runs


async def seed_tool_calls(session: AsyncSession, loads: List[Load], agent_runs: List[AgentRun]) -> List[ToolCall]:
    """Seed sample tool calls."""
    tool_call_repo = get_tool_call_repository(session)
    created_calls = []

    # Sample tool calls for demonstration
    sample_tool_calls = [
        {"tool": "send_sms", "arguments": {"recipient": "driver", "message": "Thank you for the update. ETA recorded."}, "result": {"ok": True}},
        {"tool": "update_eta", "arguments": {"eta_utc": datetime.now(timezone.utc).isoformat(), "target_location": "delivery"}, "result": {"ok": True}},
        {"tool": "create_timer", "arguments": {"timer_type": "eta_followup", "minutes": 30}, "result": {"ok": True}},
        {"tool": "update_load_state", "arguments": {"target_state": "at_delivery", "reason": "Driver arrived"}, "result": {"ok": True}},
        {"tool": "create_task", "arguments": {"task_type": "missing_load_info", "title": "Missing receiver phone"}, "result": {"ok": True}},
        {"tool": "send_slack_message", "arguments": {"audience": "broker", "message": "Missing load info task created"}, "result": {"ok": True}},
    ]

    for i, agent_run in enumerate(agent_runs[:3]):  # Create tool calls for first 3 runs
        for tool_call_data in sample_tool_calls[:2]:
            tool_call = ToolCall(
                tool_call_id=str(uuid.uuid4()),
                run_id=agent_run.run_id,
                load_id=agent_run.load_id,
                event_id=agent_run.event_id,
                tool=tool_call_data["tool"],
                arguments=tool_call_data["arguments"],
                result=tool_call_data["result"],
                created_at=datetime.now(timezone.utc),
            )
            await tool_call_repo.save(tool_call)
            created_calls.append(tool_call)

    print(f"✅ Created {len(created_calls)} tool calls")
    return created_calls


async def seed_memories(session: AsyncSession, loads: List[Load], events: List[Event]) -> List[MemoryOperationLog]:
    """Seed sample memory entries."""
    # Memory seeding skipped - requires different repository interface
    # Memory system is complex and requires proper initialization
    print("⚠️  Memory seeding skipped (requires manual setup)")
    return []


async def main():
    """Main seed function."""
    print("🌱 Starting database seeding...")
    print("=" * 60)

    # Initialize database
    db_manager = DatabaseManager("sqlite+aiosqlite:///./freighthero.db")
    await db_manager.create_tables()

    async with db_manager.async_session() as session:
        # Seed loads
        print("\n📦 Seeding loads...")
        loads = await seed_loads(session)

        # Seed events
        print("\n📨 Seeding events...")
        events = await seed_events(session, loads)

        # Seed agent runs
        print("\n🤖 Seeding agent runs...")
        agent_runs = await seed_agent_runs(session, loads, events)

        # Seed tool calls
        print("\n🔧 Seeding tool calls...")
        tool_calls = await seed_tool_calls(session, loads, agent_runs)

        # Seed memories
        print("\n🧠 Seeding memories...")
        memories = await seed_memories(session, loads, events)

        await session.commit()

    print("\n" + "=" * 60)
    print("✅ Database seeding completed successfully!")
    print(f"   - {len(loads)} loads created")
    print(f"   - {len(events)} events created")
    print(f"   - {len(agent_runs)} agent runs created")
    print(f"   - {len(tool_calls)} tool calls created")
    print(f"   - {len(memories)} memory entries created")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
