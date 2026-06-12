"""LLM initialization for FreightHero Watchtower.

Supports OpenAI, OpenRouter, and Anthropic providers.
"""

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None  # type: ignore

from src.infrastructure.config import get_settings


def get_llm():
    """Get the configured LLM instance.

    When OPENAI_BASE_URL is set (e.g. to OpenRouter),
    the ChatOpenAI client will route requests through that endpoint.

    Returns:
        A ChatOpenAI instance configured with the app settings.

    Raises:
        ImportError: If langchain-openai is not installed.
    """
    if ChatOpenAI is None:
        raise ImportError("langchain-openai is not installed. Install it with: pip install langchain-openai")

    settings = get_settings()

    kwargs: dict = {
        "model": settings.openai_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
    }

    if settings.openai_api_key:
        kwargs["api_key"] = settings.openai_api_key

    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url

    return ChatOpenAI(**kwargs)
