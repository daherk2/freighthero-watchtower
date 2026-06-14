"""Main entry point for FreightHero Watchtower."""

import uvicorn

from src.infrastructure.config import get_settings


def main() -> None:
    """Run the FreightHero Watchtower API server."""
    settings = get_settings()
    uvicorn.run(
        "src.interfaces.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()