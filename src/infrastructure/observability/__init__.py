"""Observability setup: OpenTelemetry tracing and metrics."""

import logging
from contextlib import asynccontextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from src.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


def setup_tracing() -> trace.Tracer:
    """Configure OpenTelemetry tracing.

    Returns:
        A configured tracer instance.
    """
    settings = get_settings()

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.app_version,
        }
    )

    provider = TracerProvider(resource=resource)

    if settings.otel_exporter_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return trace.get_tracer(settings.otel_service_name)


def setup_instrumentation(app=None):
    """Set up auto-instrumentation for FastAPI and HTTPX.

    Args:
        app: Optional FastAPI application instance.
    """
    if app:
        FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()


def setup_logging(log_level: str | None = None) -> None:
    """Configure structured logging.

    Args:
        log_level: Override log level. Falls back to settings.
    """
    settings = get_settings()
    level = log_level or settings.log_level
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logger.info(f"Logging configured at {level}")


def get_tracer() -> trace.Tracer:
    """Get the application tracer."""
    return trace.get_tracer(get_settings().otel_service_name)