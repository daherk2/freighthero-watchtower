# FreightHero Watchtower

AI-powered freight operations agent that monitors deliveries, manages agent workflows, and provides intelligent automation for freight operations.

## Live Demo

| | URL |
|---|---|
| **Console (Frontend)** | https://console-production-da2a.up.railway.app |
| **API (Backend)** | https://backend-production-89fb.up.railway.app |

**Access token:** `fh-wt-2026`

Use the token on the console login screen, or pass it as the `X-API-Key` header for direct API calls:

```bash
curl -H "X-API-Key: fh-wt-2026" https://backend-production-89fb.up.railway.app/api/v1/monitoring/dashboard
```

## Architecture

Follows **Hexagonal Architecture** (Ports & Adapters) with **Domain-Driven Design**:

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
│   └── services/              # Business logic
│       ├── customer_resolver.py
│       ├── sop_compiler.py
│       ├── event_processor.py
│       ├── load_service.py
│       ├── memory_manager.py
│       └── workflow_engine.py
├── agent/                     # LangGraph agent workflows
│   ├── eta_checkpoint.py      # ETA checkpoint workflow
│   ├── confirm_delivery.py    # Confirm delivery workflow
│   ├── orchestrator.py        # Workflow orchestrator
│   └── tools.py               # 13 operational tools + 6 memory tools
├── infrastructure/            # Infrastructure implementations
│   ├── config/                # Settings & configuration
│   ├── database/              # SQLAlchemy models & session management
│   ├── repositories/          # Repository implementations
│   ├── queue/                 # Celery task queue
│   └── observability/         # OpenTelemetry tracing
└── interfaces/                # API layer
    ├── app.py                 # FastAPI application
    └── routes/                # API route handlers
        ├── loads.py
        ├── events.py
        ├── monitoring.py
        └── debugger.py

console/                       # React frontend (TypeScript + MUI)
├── src/
│   ├── api/                   # API client, hooks, mock data
│   ├── components/            # Shared UI components
│   ├── screens/               # Page-level components
│   └── types/                 # TypeScript type definitions
└── vite.config.ts
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ with PGVector extension
- Redis 7+

### Backend

```bash
# Clone the repository
git clone <repo-url>
cd FreightHero

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy and configure environment variables
cp .env.example .env
```

Minimum `.env` configuration:

```env
DATABASE_URL=postgresql+asyncpg://freighthero:freighthero@localhost:5432/freighthero
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-api-key
```

### Frontend

```bash
cd console
npm install
npm run dev       # development server on http://localhost:5173
npm run build     # production build
```

### Docker (full stack)

```bash
docker-compose up -d
```

### Running Locally (without Docker)

```bash
# Start the API server
uvicorn src.interfaces.app:app --reload --port 8000

# Start the Celery worker (separate terminal)
celery -A src.infrastructure.queue worker --loglevel=info
```

### Tests

```bash
pytest tests/ -v                                      # all tests
pytest tests/ --cov=src --cov-report=term-missing     # with coverage
pytest tests/ -v -m unit                              # unit tests only
pytest tests/ -v -m agent                             # agent tests only
pytest tests/ -v -m memory                            # memory tests only
```

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/loads/` | Create a load |
| GET | `/api/v1/loads/` | List all loads |
| GET | `/api/v1/loads/{load_id}` | Get load by ID |
| POST | `/api/v1/loads/{load_id}/transition` | Transition load state |
| POST | `/api/v1/events/inbound-communication` | Submit inbound message |
| POST | `/api/v1/events/tracking` | Submit tracking event |
| POST | `/api/v1/events/load-update` | Submit load update |
| POST | `/api/v1/events/submit-task` | Submit task for agent processing |
| GET | `/api/v1/monitoring/dashboard` | Dashboard stats |
| GET | `/api/v1/monitoring/agent-runs` | Agent run history |
| GET | `/api/v1/monitoring/memory-metrics` | Memory system metrics |
| GET | `/api/v1/debugger/agent-runs/{run_id}` | Agent run detail |
| GET | `/api/v1/debugger/loads/{load_id}/history` | Load event history |
| GET | `/api/v1/debugger/memory/{scope}/{scope_id}` | Memory state |
| GET | `/api/v1/debugger/workflows` | List workflows |

All routes require the `X-API-Key` header.

## Agent Workflows

### ETA Checkpoint (`delivery_eta_checkpoint`)

Monitors delivery progress, tracking pings, arrival, and operational exceptions while a driver is en route.

**SOP Branches:**

| Branch | Trigger |
|--------|---------|
| `tracking_ping` | GPS tracking update received |
| `arrival_confirmation` | Driver arrived at delivery |
| `driver_provides_eta` | Driver sends an ETA |
| `load_information_question` | Driver asks about the load |
| `operational_issue` | Driver reports a problem |
| `broker_message` | Message from broker (no action) |
| `no_action` | No action required |

### Confirm Delivery (`confirm_delivery`)

Confirms unloading, collects proof of delivery (POD), handles lumper receipts, and escalates when needed.

**SOP Branches:**

| Branch | Trigger |
|--------|---------|
| `attachment_pod` | POD document received |
| `attachment_lumper` | Lumper receipt received |
| `attachment_other` | Unrecognized attachment |
| `unloading_started` | Unloading in progress |
| `unloading_not_started` | Unloading has not started |
| `delivery_confirmed_no_pod` | Delivery confirmed, POD missing |
| `first_arrival_contact` | First contact upon arrival |
| `operational_issue` | Operational problem reported |
| `broker_message` | Message from broker (no action) |
| `no_action` | No action required |

## Memory System

The agent uses a multi-layer memory architecture:

| Type | Storage | Purpose |
|------|---------|---------|
| **STM** | LangGraph Checkpointer | Current conversation context |
| **Episodic** | PostgreSQL + PGVector | Event-specific memories |
| **Semantic** | PostgreSQL + PGVector | Customer and load facts |
| **Procedural** | PostgreSQL + PGVector | Learned procedures |

**Memory tools:** `memory_add`, `memory_retrieve`, `memory_update`, `memory_delete`, `memory_summarize`, `memory_filter`

## Customer Configuration

| Feature | Customer A | Customer B | Customer C |
|---------|-----------|-----------|-----------|
| Escalation channel | Internal | SMS | Email |
| POD validation | Automatic | Manual | Automatic |
| Geofence radius | 1 mile | 2 miles | 0.5 miles |
| ETA timer | 30 min | 60 min | 15 min |
| Lumper handling | Review & Escalate | Review & Escalate | Auto-approve |

## Tech Stack

- **Python 3.12** · FastAPI · Pydantic v2 · SQLAlchemy (async)
- **LangGraph** for agent workflow orchestration
- **LangChain** for LLM integration (OpenAI / OpenRouter)
- **PostgreSQL 16** with PGVector for semantic memory
- **Redis** · Celery for async task processing
- **OpenTelemetry** for distributed tracing
- **React 19** · TypeScript · Material UI v6 (console)
- **Docker** for deployment
