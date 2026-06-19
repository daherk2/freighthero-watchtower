"""Test configuration and fixtures for FreightHero Watchtower."""

import asyncio
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    MemoryOperation,
    MemoryScope,
    MemoryType,
    SenderType,
    Channel,
    SOPBranch,
    ConfirmDeliveryBranch,
    AttachmentCategory,
)
from src.domain.models import Load, Event, AgentRun, ToolCall, MemoryOperationLog
from src.domain.value_objects import CustomerBehaviorConfig
from src.infrastructure.database import Base, DatabaseManager


# --- Test Database Setup ---

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_freighthero.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


# --- Domain Model Fixtures ---

@pytest.fixture
def sample_load() -> dict:
    """Sample load data for testing."""
    return {
        "load_id": f"load-{uuid.uuid4()}",
        "customer_id": CustomerId.CUSTOMER_A,
        "external_load_id": "EXT-12345",
        "po_number": "PO-67890",
        "instructions": "Deliver to dock B",
        "load_data": {
            "pickup": {
                "address": "123 Shipper St, Chicago, IL 60601",
                "appointment": "2024-01-15T08:00:00Z",
            },
            "delivery": {
                "address": "456 Receiver Ave, Milwaukee, WI 53201",
                "appointment": "2024-01-15T14:00:00Z",
                "contact": {"name": "John Receiver", "phone": "+1555123456"},
            },
            "driver": {"name": "Jane Driver", "phone": "+1555789012"},
            "trailer": {"number": "TRAIL-001"},
        },
        "current_state": LoadState.ON_ROUTE_TO_DELIVERY,
        "current_eta_utc": "2024-01-15T13:30:00Z",
    }


@pytest.fixture
def sample_inbound_communication() -> dict:
    """Sample inbound communication event data."""
    return {
        "event_id": f"evt-{uuid.uuid4()}",
        "event_type": EventType.INBOUND_COMMUNICATION,
        "load_id": "load-test-001",
        "customer_id": CustomerId.CUSTOMER_A,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "event_data": {
            "sender_type": SenderType.DRIVER,
            "channel": Channel.SMS,
            "message": "I'm about 30 minutes away from delivery",
            "attachments": [],
        },
    }


@pytest.fixture
def sample_tracking_event() -> dict:
    """Sample tracking event data."""
    return {
        "event_id": f"evt-{uuid.uuid4()}",
        "event_type": EventType.TRACKING,
        "load_id": "load-test-001",
        "customer_id": CustomerId.CUSTOMER_A,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "event_data": {
            "latitude": 43.0389,
            "longitude": -87.9065,
            "distance_to_delivery": 5.2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@pytest.fixture
def sample_customer_configs() -> dict[str, CustomerBehaviorConfig]:
    """Sample customer behavior configurations."""
    return {
        "customer_a": CustomerBehaviorConfig(
            customer_id=CustomerId.CUSTOMER_A,
            escalation_channel="email",
            missing_load_info_action="create_task",
            pod_validation_type="automatic",
            pod_received_visibility="notify_escalation_channel",
            delivered_without_pod_visibility="notify_escalation_channel",
            delivery_geofence_radius_miles=1,
            eta_followup_timer_minutes=30,
            lumper_receipt_handling="classify_and_create_review_task",
            first_arrival_message="Ask for unloading status and POD when available.",
        ),
        "customer_b": CustomerBehaviorConfig(
            customer_id=CustomerId.CUSTOMER_B,
            escalation_channel="slack",
            missing_load_info_action="create_task_and_send_visibility",
            pod_validation_type="human_review",
            pod_received_visibility="no_notification",
            delivered_without_pod_visibility="no_notification",
            delivery_geofence_radius_miles=2,
            eta_followup_timer_minutes=60,
            lumper_receipt_handling="classify_and_create_review_task",
            first_arrival_message="Ask driver to confirm unloading start and send POD when empty.",
        ),
        "customer_c": CustomerBehaviorConfig(
            customer_id=CustomerId.CUSTOMER_C,
            escalation_channel="email_and_slack",
            missing_load_info_action="create_task",
            pod_validation_type="automatic",
            pod_received_visibility="notify_escalation_channel",
            delivered_without_pod_visibility="notify_escalation_channel",
            delivery_geofence_radius_miles=3,
            eta_followup_timer_minutes=45,
            lumper_receipt_handling="forward_email_if_lumper_else_review_task",
            first_arrival_message="Ask for unloading updates, POD, and any lumper receipt when available.",
        ),
    }


# --- Pytest Configuration ---

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "agent: Agent workflow tests")
    config.addinivalue_line("markers", "memory: Memory system tests")
    config.addinivalue_line("markers", "slow: Slow tests")