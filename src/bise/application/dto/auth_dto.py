"""DTOs for workspaces and API keys."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class WorkspaceDTO:
    """Output: a workspace."""

    id: int | None
    name: str
    slug: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ApiKeyDTO:
    """Output: an API key's metadata (never the raw secret)."""

    id: int | None
    workspace_id: int
    name: str
    prefix: str
    revoked: bool
    last_used_at: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class CreatedApiKeyDTO:
    """Output: a newly created key, including the raw secret shown exactly once."""

    api_key: ApiKeyDTO
    secret: str
