"""Engine and session factory construction from settings.

This is the SQLite/PostgreSQL swap point: the URL comes from configuration, and
SQLite-specific connection tuning (foreign-key enforcement, thread sharing) is
applied only when the URL is SQLite.
"""

from __future__ import annotations

from typing import Any

from config.settings import Settings
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def create_db_engine(settings: Settings) -> Engine:
    """Create a SQLAlchemy engine tuned for the configured backend."""
    connect_args: dict[str, Any] = {}
    if settings.is_sqlite:
        connect_args["check_same_thread"] = False

    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        future=True,
        connect_args=connect_args,
    )

    if settings.is_sqlite:
        # SQLite disables foreign-key enforcement by default; turn it on so the
        # dev database behaves like PostgreSQL.
        @event.listens_for(engine, "connect")
        def _enable_sqlite_fk(dbapi_connection: Any, _record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a configured session factory bound to the engine."""
    return sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
