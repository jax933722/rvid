"""Typed, validated application settings (12-factor).

This is the single source of configuration. Nothing in the codebase reads
``os.environ`` directly — everything goes through :func:`get_settings`.

The database URL is the SQLite/PostgreSQL swap seam: ``sqlite:///./bise.db``
for development, ``postgresql+psycopg://...`` for production, chosen entirely by
the ``BISE_DATABASE_URL`` environment variable with no code change.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "prod"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
SearchBackend = Literal["postgres_fts", "opensearch"]


class Settings(BaseSettings):
    """Application configuration, validated on load.

    Values are read from environment variables (prefixed ``BISE_``) or a local
    ``.env`` file. Invalid or missing-but-required values fail fast at startup.
    """

    model_config = SettingsConfigDict(
        env_prefix="BISE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    # --- Application ---
    env: Environment = "local"
    debug: bool = True

    # --- Database (SQLite dev / PostgreSQL prod behind one URL) ---
    database_url: str = Field(
        default="sqlite:///./bise.db",
        description="SQLAlchemy URL: sqlite:// for dev, postgresql+psycopg:// for prod.",
    )
    db_echo: bool = False

    # --- Search backend (FTS now -> OpenSearch later) ---
    search_backend: SearchBackend = "postgres_fts"

    # --- Logging ---
    log_level: LogLevel = "INFO"
    log_json: bool = True

    @field_validator("database_url")
    @classmethod
    def _database_url_not_empty(cls, value: str) -> str:
        if not value or "://" not in value:
            raise ValueError(
                "database_url must be a valid SQLAlchemy URL, e.g. sqlite:///./bise.db"
            )
        return value

    @property
    def is_sqlite(self) -> bool:
        """True when the configured database is SQLite (affects engine options)."""
        return self.database_url.startswith("sqlite")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton (cached after first load)."""
    return Settings()
