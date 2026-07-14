"""``CompanyList`` — a named collection of companies (lists & bookmarks).

The list is the aggregate root; membership is a persistence concern handled by
the repository (a company can belong to many lists). ``member_count`` is a
read-only projection the repository fills in when loading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from bise.domain.errors import InvalidValueError


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class CompanyList:
    """A user-named list of companies (also used for bookmarking)."""

    name: str
    description: str | None = None
    member_count: int = 0
    workspace_id: int | None = None
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidValueError("CompanyList.name must be a non-empty string")
        self.name = self.name.strip()
        if self.description is not None:
            self.description = self.description.strip() or None
