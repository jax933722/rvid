"""``ApiKey`` — a hashed credential granting access to one workspace.

The raw key is shown to the user exactly once at creation and never stored; only
its SHA-256 hash and a short display prefix are persisted. Authentication hashes
the presented key and looks it up by hash.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from bise.domain.errors import InvalidValueError


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class ApiKey:
    """A workspace-scoped API credential (stored hashed)."""

    workspace_id: int
    name: str
    key_hash: str
    prefix: str
    revoked: bool = False
    last_used_at: datetime | None = None
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidValueError("ApiKey.name must be a non-empty string")
        self.name = self.name.strip()
        if not self.key_hash:
            raise InvalidValueError("ApiKey.key_hash must be set")

    @property
    def is_active(self) -> bool:
        """Whether the key may still authenticate."""
        return not self.revoked
