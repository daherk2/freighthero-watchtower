# Database Seeding Guide

This guide explains how to populate the FreightHero Watchtower database with realistic demo data for demonstration and testing purposes.

## Quick Start

### Using the Seed Script

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the seed script
python scripts/seed_database.py
```

### Expected Output

```
🌱 Starting database seeding...
============================================================

📦 Seeding loads...
✅ Created load: load-customer-a-001 (customer_a) - State: at_delivery
✅ Created load: load-customer-b-002 (customer_b) - State: on_route_to_delivery
✅ Created load: load-customer-c-003 (customer_c) - State: pod_collected

📨 Seeding events...
✅ Created event: evt-a-... (inbound_communication) for load load-customer-a-001
✅ Created event: evt-a-... (inbound_communication) for load load-customer-a-001
✅ Created event: evt-b-... (inbound_communication) for load load-customer-b-002
✅ Created event: evt-b-... (tracking) for load load-customer-b-002
✅ Created event: evt-c-... (inbound_communication) for load load-customer-c-003

🤖 Seeding agent runs...
✅ Created agent run: run-... for load load-customer-a-001
✅ Created agent run: run-... for load load-customer-b-002
✅ Created agent run: run-... for load load-customer-c-003

🔧 Seeding tool calls...
✅ Created 6 tool calls

🧠 Seeding memories...
✅ Created 3 memory entries

============================================================
✅ Database seeding completed successfully!
   - 3 loads created
   - 5 events created
   - 3 agent runs created
   - 6 tool calls created
   - 3 memory entries created
============================================================
```

## What Gets Seeded

### Loads

Three sample loads are created, one for each customer type:

| Load ID | Customer | State | Description |
|---------|----------|-------|-------------|
| `load-customer-a-001` | Customer A | `at_delivery` | Driver arrived, unloading started |
| `load-customer-b-002` | Customer B | `on_route_to_delivery` | En route, ETA in 5 hours |
| `load-customer-c-003` | Customer C | `pod_collected` | Delivery complete with POD |

### Events

Sample events demonstrating different SOP branches:

**Customer A (at_delivery):**
- Driver arrival SMS
- Unloading started notification

**Customer B (on_route_to_delivery):**
- Driver asking for appointment time
- GPS tracking ping

**Customer C (pod_collected):**
- Email with POD attachment

### Agent Runs

Pre-populated agent runs showing:
- Workflow selection
- SOP branch classification
- Tool call execution
- Memory operations

### Tool Calls

Sample tool calls demonstrating:
- `send_sms` - Driver communication
- `update_eta` - ETA updates
- `create_timer` - Follow-up scheduling
- `update_load_state` - State transitions
- `create_task` - Human task creation
- `send_slack_message` - Broker notifications

### Memory Entries

Semantic memory entries for each load demonstrating:
- Customer preference learning
- Agent-driven memory operations
- Confidence scoring

## Database Configuration

The seed script uses SQLite by default for easy demo setup:

```python
DATABASE_URL = "sqlite+aiosqlite:///./freighthero.db"
```

### Using PostgreSQL

To seed a PostgreSQL database instead:

1. Update the database URL in `scripts/seed_database.py`:
```python
db_manager = DatabaseManager("postgresql+asyncpg://freighthero:freighthero@localhost:5432/freighthero")
```

2. Ensure PostgreSQL is running with PGVector extension enabled

3. Run the seed script

## Viewing Seeded Data

After seeding, you can view the data through:

### API Endpoints

```bash
# Get all loads
curl http://localhost:8000/api/v1/loads/

# Get specific load
curl http://localhost:8000/api/v1/loads/load-customer-a-001

# Get monitoring dashboard
curl http://localhost:8000/api/v1/monitoring/dashboard

# Get agent runs
curl http://localhost:8000/api/v1/debugger/agent-runs
```

### Console UI

Navigate to the console application to view:
- **Dashboard**: Overview of all loads
- **Loads**: Detailed load information
- **Agent Viewer**: Agent execution history
- **Memory Explorer**: Memory entries by type
- **Tool Calls**: Tool call history and outputs

## Resetting the Database

To reset and re-seed:

```bash
# Delete the SQLite database
rm freighthero.db

# Re-run the seed script
python scripts/seed_database.py
```

For PostgreSQL:

```bash
# Drop and recreate the database
psql -U freighthero -c "DROP DATABASE IF EXISTS freighthero;"
psql -U freighthero -c "CREATE DATABASE freighthero;"

# Re-run the seed script
python scripts/seed_database.py
```

## Customizing Seed Data

To customize the seed data for your demo scenarios:

1. Edit `SAMPLE_LOADS` in `scripts/seed_database.py`
2. Modify event content and timing
3. Add custom tool calls
4. Create specific memory entries

### Example: Adding a Load with Operational Issue

```python
{
    "load_id": "load-issue-demo",
    "customer_id": CustomerId.CUSTOMER_A,
    "current_state": LoadState.ON_ROUTE_TO_DELIVERY,
    # ... other fields
}
```

Then add an event with operational issue:

```python
Event(
    event_type=EventType.INBOUND_COMMUNICATION,
    event_data=InboundCommunication(
        channel=Channel.SMS,
        sender_type=SenderType.DRIVER,
        content="Truck broke down, need roadside assistance.",
    ),
)
```

## Demo Scenarios

### Scenario 1: Customer A - Automatic POD Validation

1. Show load `load-customer-a-001` in `at_delivery` state
2. Demonstrate arrival confirmation workflow
3. Show SMS communication with driver
4. When POD arrives, show automatic validation

### Scenario 2: Customer B - Human POD Review

1. Show load `load-customer-b-002` in `on_route_to_delivery` state
2. Demonstrate ETA checkpoint workflow
3. Show Slack escalation for missing info
4. When POD arrives, show human review task creation

### Scenario 3: Customer C - Dual Escalation

1. Show load `load-customer-c-003` in `pod_collected` state
2. Demonstrate completed delivery workflow
3. Show email + Slack dual escalation
4. Show lumper receipt forwarding (if applicable)

## Troubleshooting

### Database Already Exists

If you get errors about existing data:

```bash
# For SQLite
rm freighthero.db
python scripts/seed_database.py

# For PostgreSQL
# Drop all tables first, then re-seed
```

### Import Errors

Ensure virtual environment is activated:

```bash
source .venv/bin/activate
python scripts/seed_database.py
```

### Database Connection Errors

Verify database is running:

```bash
# PostgreSQL
docker-compose ps

# Or check directly
psql -U freighthero -d freighthero -c "SELECT 1"
```

## Next Steps

After seeding the database:

1. Start the API server: `uvicorn src.interfaces.app:app --reload`
2. Start the console: `cd console && npm run dev`
3. Navigate to the console UI
4. Explore the seeded data
5. Run additional events through the API

---

**Last Updated:** June 12, 2026  
**Script Version:** 1.0  
**Compatible With:** FreightHero Watchtower v0.1.0
