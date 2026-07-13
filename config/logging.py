"""Structured logging configuration (structlog).

Produces JSON logs in production and human-friendly console logs in development.
A ``correlation_id`` is bound per request/job so a single pipeline run can be
traced across the API and workers.
"""

from __future__ import annotations

import logging
from typing import Any

import structlog

from config.settings import LogLevel


def configure_logging(*, level: LogLevel = "INFO", json_output: bool = True) -> None:
    """Configure structlog + stdlib logging once, at process startup.

    Args:
        level: Minimum log level to emit.
        json_output: Emit machine-readable JSON (prod) vs. pretty console (dev).
    """
    logging.basicConfig(format="%(message)s", level=getattr(logging, level))

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer: Any = (
        structlog.processors.JSONRenderer() if json_output else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given module name."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger


def bind_correlation_id(correlation_id: str) -> None:
    """Bind a correlation id to the current context (request/job scope)."""
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def clear_correlation_id() -> None:
    """Clear context-local bindings at the end of a request/job."""
    structlog.contextvars.clear_contextvars()
