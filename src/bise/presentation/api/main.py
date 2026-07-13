"""FastAPI application factory.

The app is created via a factory so tests can inject a container backed by an
in-memory SQLite database, while production uses the default (settings-driven)
container.
"""

from __future__ import annotations

from config.containers import Container
from config.logging import configure_logging
from config.settings import get_settings
from fastapi import FastAPI

from bise import __version__
from bise.presentation.api.errors import register_exception_handlers
from bise.presentation.api.routers import companies, crawlers, health, technologies

API_PREFIX = "/api/v1"


def create_app(container: Container | None = None) -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)

    app = FastAPI(
        title="Business Intelligence Search Engine",
        version=__version__,
        description="Searchable index of publicly available business information.",
    )
    app.state.container = container or Container(settings)

    register_exception_handlers(app)
    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(companies.router, prefix=API_PREFIX)
    app.include_router(crawlers.router, prefix=API_PREFIX)
    app.include_router(technologies.router, prefix=API_PREFIX)
    return app


app = create_app()
