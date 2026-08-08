"""Unit tests for Workspace and ApiKey entities."""

from __future__ import annotations

import pytest

from bise.domain.entities.api_key import ApiKey
from bise.domain.entities.workspace import Workspace, slugify
from bise.domain.errors import InvalidValueError


def test_workspace_derives_slug_from_name() -> None:
    ws = Workspace(name="Acme Sales Team")
    assert ws.slug == "acme-sales-team"


def test_workspace_explicit_slug_is_normalized() -> None:
    assert Workspace(name="X", slug="My Slug!").slug == "my-slug"


def test_workspace_requires_name() -> None:
    with pytest.raises(InvalidValueError):
        Workspace(name="  ")


def test_slugify_collapses_non_alnum() -> None:
    assert slugify("  Hello, World -- 2026 ") == "hello-world-2026"


def test_api_key_requires_name_and_hash() -> None:
    with pytest.raises(InvalidValueError):
        ApiKey(workspace_id=1, name="", key_hash="h", prefix="p")
    with pytest.raises(InvalidValueError):
        ApiKey(workspace_id=1, name="k", key_hash="", prefix="p")


def test_api_key_active_unless_revoked() -> None:
    key = ApiKey(workspace_id=1, name="k", key_hash="h", prefix="bise_abc")
    assert key.is_active
    key.revoked = True
    assert not key.is_active
