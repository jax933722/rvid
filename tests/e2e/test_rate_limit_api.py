"""End-to-end tests for request rate limiting."""

from __future__ import annotations

from pathlib import Path

from config.containers import Container
from config.settings import Settings
from fastapi.testclient import TestClient

import bise.infrastructure.db.models  # noqa: F401  (register tables)
from bise.infrastructure.db.base import Base
from bise.presentation.api.main import create_app


def _client(tmp_path: Path, **overrides: object) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'rl.db'}",
        env="test",
        log_json=False,
        **overrides,  # type: ignore[arg-type]
    )
    container = Container(settings)
    Base.metadata.create_all(container.engine)
    return TestClient(create_app(container))


def test_exceeding_limit_returns_429_with_retry_after(tmp_path: Path) -> None:
    client = _client(
        tmp_path, rate_limit_enabled=True, rate_limit_per_minute=60, rate_limit_burst=2
    )
    # Two requests fit the burst; the third is throttled.
    assert client.get("/api/v1/companies").status_code == 200
    ok = client.get("/api/v1/companies")
    assert ok.status_code == 200
    assert ok.headers["X-RateLimit-Limit"] == "2"

    limited = client.get("/api/v1/companies")
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) >= 1
    assert limited.headers["X-RateLimit-Remaining"] == "0"


def test_health_is_exempt_from_rate_limit(tmp_path: Path) -> None:
    client = _client(
        tmp_path, rate_limit_enabled=True, rate_limit_per_minute=60, rate_limit_burst=1
    )
    # Health never counts against the bucket, so it always answers.
    for _ in range(5):
        assert client.get("/api/v1/health").status_code == 200


def test_disabling_rate_limit_lets_everything_through(tmp_path: Path) -> None:
    client = _client(tmp_path, rate_limit_enabled=False)
    for _ in range(10):
        assert client.get("/api/v1/companies").status_code == 200
    # No rate-limit headers when the middleware is off.
    assert "X-RateLimit-Limit" not in client.get("/api/v1/companies").headers


def test_distinct_api_keys_have_separate_budgets(tmp_path: Path) -> None:
    client = _client(
        tmp_path, rate_limit_enabled=True, rate_limit_per_minute=60, rate_limit_burst=1
    )
    a = {"Authorization": "Bearer key-a"}
    b = {"Authorization": "Bearer key-b"}
    assert client.get("/api/v1/companies", headers=a).status_code == 200
    assert client.get("/api/v1/companies", headers=a).status_code == 429
    # A different key still has its own token.
    assert client.get("/api/v1/companies", headers=b).status_code == 200
