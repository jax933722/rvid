"""``CompanyTag`` — a free-form label attached to a company.

Tags are lightweight, case-insensitive labels for organizing prospects
(e.g. "priority", "contacted"). Normalized to a trimmed, lowercased form so
"Priority" and "priority" collapse to one tag per company.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from bise.domain.errors import InvalidValueError


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class CompanyTag:
    """A normalized label applied to a company."""

    company_id: int
    label: str
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidValueError("CompanyTag.label must be a non-empty string")
        self.label = self.label.strip().lower()
