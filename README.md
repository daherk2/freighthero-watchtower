# FreightHero Watchtower

AI-powered freight operations agent that monitors deliveries, manages agent workflows, and provides intelligent automation for freight operations.

## Access

| | URL |
|---|---|
| **Frontend (Console)** | https://console-production-da2a.up.railway.app |
| **Backend (API)** | https://backend-production-89fb.up.railway.app |

**Access token:** `fh-wt-2026`

Use the token above on the console login screen, or pass it as the `X-API-Key` header for direct API calls:

```bash
curl -H "X-API-Key: fh-wt-2026" https://backend-production-89fb.up.railway.app/api/v1/monitoring/dashboard
```

## Architecture

The system follows **Hexagonal Architecture** (Ports & Adapters) with **Domain-Driven Design** principles:

```
┌─────────────────────────────────────────────────────────┐
│                    Interfaces Layer                       │
│  (FastAPI routes, request/response DTOs)                 │
├─────────────────────────────────────────────────────────┤
│                    Application Layer                      │
│  (Services, Ports, DTOs)                                 │
├─────────────────────────────────────────────────────────┤
│                    Agent Layer                            │
│  (LangGraph workflows, Tools, Orchestrator)              │
├─────────────────────────────────────────────────────────┤
│                    Domain Layer                           │
│  (Models, Value Objects, Enums, Events, Exceptions)      │
├─────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                   │
│  (Database, Queue, Observability, Repositories)          │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
src/
├── domain/                    # Core domain logic
│   ├── enums/                 # Domain enumerations
│   ├── exceptions/            # Domain exceptions
│   ├── models/                # Domain entities
│   ├── value_objects/         # Value objects
│   └── events/                # Domain events
├── application/               # Application services
│   ├── ports/                 # Abstract interfaces
│   ├── dto/                   # Data transfer objects
│   └── services/             # Business logic
│       ├── customer_resolver.py
│       ├── sop_compiler.py
│       ├── event_processor.py
│       ├── load_service.py
│       ├── memory_manager.py
│       └── workflow_engine.py
├── agent/                     # Agent workflows
│   ├── eta_checkpoint.py      # ETA checkpoint LangGraph workflow
│   ├── confirm_delivery.py    # Confirm delivery LangGraph workflow
│   ├── orchestrator.py        # Agent orchestrator
│   └── tools.py               # 13 mock tools + 6 memory tools
├── infrastructure/             # Infrastructure implementations
│   ├── config/                # Settings & configuration
│   ├── database/              # SQLAlchemy models & session management
│   ├── repositories/          # Repository implementations
│   ├── queue/                 # Celery task queue
│   └── observability/         # OpenTelemetry tracing
└── interfaces/                 # API layer
    ├── app.py                 # FastAPI application
    └── routes/                # API routes
        ├── loads.py
        ├── events.py
        ├── monitoring.py
        └── debugger.py
```

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 16+ with PGVector extension
- Redis 7+

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd FreightHero

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql+asyncpg://freighthero:freighthero@localhost:5432/freighthero
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-api-key
```

### Running with Docker

```bash
docker-compose up -d
```

### Running Locally

```bash
# Start the API server
uvicorn src.interfaces.app:app --reload --port 8000

# Start the Celery worker
celery -A src.infrastructure.queue worker --loglevel=info
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test categories
pytest tests/ -v -m unit
pytest tests/ -v -m agent
pytest tests/ -v -m memory
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/loads/` | Create a new load |
| GET | `/api/v1/loads/` | Get active loads |
| GET | `/api/v1/loads/{load_id}` | Get load by ID |
| POST | `/api/v1/loads/{load_id}/transition` | Transition load state |
| POST | `/api/v1/events/inbound-communication` | Submit inbound communication |
| POST | `/api/v1/events/tracking` | Submit tracking event |
| POST | `/api/v1/events/load-update` | Submit load update |
| POST | `/api/v1/events/submit-task` | Submit task for agent processing |
| GET | `/api/v1/monitoring/dashboard` | Monitoring dashboard |
| GET | `/api/v1/monitoring/agent-runs` | Agent run history |
| GET | `/api/v1/monitoring/memory-metrics` | Memory system metrics |
| GET | `/api/v1/debugger/agent-runs/{run_id}` | Agent run details |
| GET | `/api/v1/debugger/loads/{load_id}/history` | Load history |
| GET | `/api/v1/debugger/memory/{scope}/{scope_id}` | Memory state |
| GET | `/api/v1/debugger/workflows` | List workflows |

## Agent Workflows

### ETA Checkpoint (`delivery_eta_checkpoint`)

Monitors delivery ETA, tracking, arrival, and operational exceptions while a driver is en route.

**SOP Branches:**
- `tracking_ping` - GPS tracking update
- `arrival_confirmation` - Driver arrived at delivery
- `driver_provides_eta` - Driver provides ETA
- `load_information_question` - Driver asks about load
- `operational_issue` - Driver reports problem
- `broker_message` - Broker message (no action)
- `no_action` - No action needed

### Confirm Delivery (`confirm_delivery`)

Confirms unloading, collects POD, handles lumper receipts, and escalates when needed.

**SOP Branches:**
- `attachment_pod` - POD document received
- `attachment_lumper` - Lumper receipt received
- `attachment_other` - Unrecognized attachment
- `unloading_started` - Unloading in progress
- `unloading_not_started` - Unloading hasn't started
- `delivery_confirmed_no_pod` - Delivery confirmed without POD
- `first_arrival_contact` - First arrival at delivery
- `operational_issue` - Operational problem
- `broker_message` - Broker message (no action)
- `no_action` - No action needed

## Memory Architecture

The agent uses a multi-layer memory system:

| Type | Storage | Purpose |
|------|---------|---------|
| **STM** | LangGraph Checkpointer | Current conversation context |
| **Episodic** | PostgreSQL + PGVector | Event-specific memories |
| **Semantic** | PostgreSQL + PGVector | Customer/load facts |
| **Procedural** | PostgreSQL + PGVector | Learned procedures |

**Memory Tools (6):**
1. `memory_add` - Add new memory
2. `memory_retrieve` - Retrieve memories
3. `memory_update` - Update existing memory
4. `memory_delete` - Delete memory
5. `memory_summarize` - Compress memories
6. `memory_filter` - Remove low-relevance memories

## Customer Behavior Matrix

| Feature | Customer A | Customer B | Customer C |
|---------|-----------|-----------|-----------|
| Escalation Channel | Internal | SMS | Email |
| POD Validation | Automatic | Manual | Automatic |
| Geofence Radius | 1 mile | 2 miles | 0.5 miles |
| ETA Timer | 30 min | 60 min | 15 min |
| Lumper Handling | Review & Escalate | Review & Escalate | Auto-approve |

## Tech Stack

- **Python 3.12+** with FastAPI
- **LangGraph** for agent workflow orchestration
- **LangChain** for LLM integration
- **Pydantic v2** for data validation
- **SQLAlchemy** with async PostgreSQL
- **PGVector** for semantic search
- **Redis** for caching and queues
- **Celery** for async task processing
- **OpenTelemetry** for observability
- **Docker** + **Terraform** for deployment