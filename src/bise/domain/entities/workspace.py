"""``Workspace`` — a tenant boundary for a user's own prospecting work.

Workspaces isolate *personal* data (saved searches, lists, tags). The company
index and Prospector search are shared public data and are not workspace-scoped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from bise.domain.errors import InvalidValueError

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def slugify(value: str) -> str:
    """Normalize a name into a URL-safe slug (lowercase, hyphen-separated)."""
    return _SLUG_RE.sub("-", value.strip().lower()).strip("-")


@dataclass(slots=True)
class Workspace:
    """A tenant owning its saved searches, lists, and tags."""

    name: str
    slug: str = ""
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidValueError("Workspace.name must be a non-empty string")
        self.name = self.name.strip()
        self.slug = slugify(self.slug) if self.slug else slugify(self.name)
        if not self.slug:
            raise InvalidValueError("Workspace.slug could not be derived from the name")
