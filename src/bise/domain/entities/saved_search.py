"""``SavedSearch`` — a named, reusable Prospector query.

Stores the search request payload as an opaque JSON string. The domain does not
interpret the payload; it only guards the name invariant. The application layer
serializes/deserializes the query on the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from bise.domain.errors import InvalidValueError


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class SavedSearch:
    """A user-named saved Prospector search."""

    name: str
    query_json: str
    workspace_id: int | None = None
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidValueError("SavedSearch.name must be a non-empty string")
        self.name = self.name.strip()
        if not self.query_json or not self.query_json.strip():
            raise InvalidValueError("SavedSearch.query_json must be a non-empty string")
