"""FastAPI application for FreightHero Watchtower.

This module creates and configures the FastAPI application with
all routes, middleware, and lifecycle management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.infrastructure.config import get_settings
from src.infrastructure.database import DatabaseManager
from src.infrastructure.observability import setup_tracing, setup_logging, setup_instrumentation, get_tracer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Sets up database connections, tracing, and other resources
    on startup, and cleans them up on shutdown.
    """
    settings = get_settings()

    # Setup logging
    setup_logging(settings.log_level)

    # Setup tracing
    tracer = setup_tracing()

    # Setup database
    db_manager = DatabaseManager(settings.database_url)
    await db_manager.create_tables()
    app.state.db_manager = db_manager
    app.state.settings = settings

    yield

    # Cleanup
    await db_manager.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="FreightHero Watchtower",
        description="AI-powered freight operations agent",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API key auth middleware (skip /health)
    @app.middleware("http")
    async def require_api_key(request: Request, call_next):
        if request.url.path == "/health" or request.method == "OPTIONS":
            return await call_next(request)
        key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if key != settings.api_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
        return await call_next(request)

    # Setup OpenTelemetry instrumentation
    setup_instrumentation(app)

    # Register routers
    from src.interfaces.routes import loads, events, monitoring, debugger

    app.include_router(loads.router, prefix="/api/v1/loads", tags=["loads"])
    app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
    app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
    app.include_router(debugger.router, prefix="/api/v1/debugger", tags=["debugger"])

    # Health check
    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "healthy", "version": settings.app_version}

    return app


# Create the app instance
app = create_app()