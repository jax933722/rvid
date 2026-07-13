"""Shared pytest fixtures.

Integration and e2e tests run against a real but throwaway file-based SQLite
database, so they need no external services yet exercise the real SQLAlchemy
adapters end to end.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from config.containers import Container
from config.settings import Settings
from fastapi.testclient import TestClient

import bise.infrastructure.db.models  # noqa: F401  (registers all tables on Base.metadata)
from bise.infrastructure.db.base import Base
from bise.presentation.api.main import create_app


@pytest.fixture
def container(tmp_path: Path) -> Container:
    """A container wired to a fresh SQLite database with the schema created."""
    db_path = tmp_path / "test.db"
    settings = Settings(database_url=f"sqlite:///{db_path}", env="test", log_json=False)
    container = Container(settings)
    Base.metadata.create_all(container.engine)
    return container


@pytest.fixture
def client(container: Container) -> Iterator[TestClient]:
    """A FastAPI test client backed by the SQLite-backed container."""
    app = create_app(container)
    with TestClient(app) as test_client:
        yield test_client
