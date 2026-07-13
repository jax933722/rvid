"""Unit tests for application settings."""

from __future__ import annotations

import pytest
from config.settings import Settings
from pydantic import ValidationError


def test_defaults_to_sqlite_dev() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.is_sqlite
    assert settings.env == "local"


def test_postgres_url_is_not_sqlite() -> None:
    settings = Settings(database_url="postgresql+psycopg://u:p@localhost/bise", _env_file=None)  # type: ignore[call-arg]
    assert not settings.is_sqlite


def test_rejects_malformed_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="not-a-url", _env_file=None)  # type: ignore[call-arg]
