"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "freighthero-watchtower"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://freighthero:freighthero@localhost:5432/freighthero"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str = ""  # For OpenRouter: https://openrouter.ai/api/v1
    openai_fallback_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    # LangGraph
    langgraph_checkpointer: str = "postgres"  # postgres or sqlite
    langgraph_checkpointer_url: str = ""  # Uses database_url if empty

    # Memory
    memory_stm_max_tokens: int = 4000
    memory_stm_max_events: int = 20
    memory_ltm_table: str = "ltm_memory"
    memory_embedding_model: str = "text-embedding-3-small"
    memory_embedding_dimensions: int = 1536

    # Observability
    otel_exporter_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "freighthero-watchtower"
    langsmith_api_key: str = ""
    langsmith_project: str = "freighthero-watchtower"

    # Geofence defaults
    default_geofence_radius_miles: int = 1

    # Timer defaults
    default_eta_followup_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()