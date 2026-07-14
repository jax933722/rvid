"""End-to-end tests for workspaces, API keys, and opt-in auth enforcement."""

from __future__ import annotations

from pathlib import Path

import pytest
from config.containers import Container
from config.settings import Settings
from fastapi.testclient import TestClient

import bise.infrastructure.db.models  # noqa: F401  (register tables)
from bise.infrastructure.db.base import Base
from bise.presentation.api.main import create_app


def _client(db_url: str, *, auth_enabled: bool) -> TestClient:
    settings = Settings(
        database_url=db_url, env="test", log_json=False, auth_enabled=auth_enabled
    )
    container = Container(settings)
    Base.metadata.create_all(container.engine)
    return TestClient(create_app(container))


@pytest.fixture
def shared_db(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'auth.db'}"


def test_default_workspace_when_auth_disabled(client: TestClient) -> None:
    res = client.get("/api/v1/auth/whoami")
    assert res.status_code == 200
    assert res.json()["slug"] == "default"


def test_create_list_revoke_api_key(client: TestClient) -> None:
    created = client.post("/api/v1/api-keys", json={"name": "CI"})
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["secret"].startswith("bise_")
    assert body["api_key"]["prefix"] == body["secret"][:12]
    key_id = body["api_key"]["id"]

    listed = client.get("/api/v1/api-keys")
    assert [k["name"] for k in listed.json()] == ["CI"]
    assert listed.json()[0]["revoked"] is False

    assert client.delete(f"/api/v1/api-keys/{key_id}").status_code == 204
    assert client.get("/api/v1/api-keys").json()[0]["revoked"] is True


def test_auth_enforced_requires_valid_key(shared_db: str) -> None:
    # Mint a key with auth OFF (bootstrap), then enforce with a second app.
    with _client(shared_db, auth_enabled=False) as bootstrap:
        secret = bootstrap.post("/api/v1/api-keys", json={"name": "prod"}).json()["secret"]

    with _client(shared_db, auth_enabled=True) as secured:
        # No key -> 401.
        assert secured.get("/api/v1/lists").status_code == 401
        # Bad key -> 401.
        bad = secured.get("/api/v1/lists", headers={"Authorization": "Bearer nope"})
        assert bad.status_code == 401
        # Valid key -> 200, and it resolves to the default workspace.
        ok = secured.get("/api/v1/lists", headers={"Authorization": f"Bearer {secret}"})
        assert ok.status_code == 200
        who = secured.get("/api/v1/auth/whoami", headers={"X-API-Key": secret})
        assert who.status_code == 200
        assert who.json()["slug"] == "default"


def test_public_search_needs_no_key_even_when_auth_enabled(shared_db: str) -> None:
    # Search is shared public data and is not workspace-scoped, so it stays open.
    with _client(shared_db, auth_enabled=True) as secured:
        res = secured.post(
            "/api/v1/search",
            json={"filters": [], "facets": [], "page": 1, "page_size": 25},
        )
        assert res.status_code == 200


def test_revoked_key_is_rejected(shared_db: str) -> None:
    with _client(shared_db, auth_enabled=False) as bootstrap:
        created = bootstrap.post("/api/v1/api-keys", json={"name": "temp"}).json()
        secret = created["secret"]
        key_id = created["api_key"]["id"]
        assert bootstrap.delete(f"/api/v1/api-keys/{key_id}").status_code == 204

    with _client(shared_db, auth_enabled=True) as secured:
        res = secured.get("/api/v1/lists", headers={"Authorization": f"Bearer {secret}"})
        assert res.status_code == 401
