"""``LeadCampaign`` — a standing ICP that keeps surfacing fresh leads.

A campaign defines *what* you want (business categories) and *where* (locations),
plus how often to run. Each run sweeps the next cell of the category×location grid
via a rotating cursor, so successive runs keep discovering businesses you haven't
seen — the mechanism that makes lead generation continuous rather than one-shot.

No paid APIs: discovery runs against the free OpenStreetMap source already wired
into BISE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from bise.domain.errors import InvalidValueError


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _clean(values: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        trimmed = value.strip()
        if trimmed:
            seen.setdefault(trimmed, None)
    return list(seen)


@dataclass(slots=True)
class LeadCampaign:
    """A recurring discovery campaign for one ideal-customer profile."""

    name: str
    categories: list[str]
    locations: list[str]
    interval_minutes: int = 60
    is_active: bool = True
    auto_enrich: bool = True
    per_run_limit: int = 50
    # Rotation cursor over the flattened category×location grid.
    cursor: int = 0
    last_run_at: datetime | None = None
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidValueError("LeadCampaign.name must be a non-empty string")
        self.name = self.name.strip()
        self.categories = _clean(self.categories)
        self.locations = _clean(self.locations)
        if not self.categories:
            raise InvalidValueError("LeadCampaign requires at least one category")
        if not self.locations:
            raise InvalidValueError("LeadCampaign requires at least one location")
        if self.interval_minutes < 1:
            raise InvalidValueError("LeadCampaign.interval_minutes must be >= 1")
        if not 1 <= self.per_run_limit <= 200:
            raise InvalidValueError("LeadCampaign.per_run_limit must be within [1, 200]")

    @property
    def grid_size(self) -> int:
        """Total number of (category, location) cells in the sweep."""
        return len(self.categories) * len(self.locations)

    def current_target(self) -> tuple[str, str]:
        """The (category, location) the cursor currently points at."""
        index = self.cursor % self.grid_size
        category = self.categories[index % len(self.categories)]
        location = self.locations[index // len(self.categories)]
        return category, location

    def advance(self) -> None:
        """Move the cursor to the next grid cell and record the run time."""
        self.cursor = (self.cursor + 1) % self.grid_size
        self.last_run_at = _utcnow()
        self.updated_at = _utcnow()

    def is_due(self, now: datetime | None = None) -> bool:
        """Whether this active campaign is due to run again."""
        if not self.is_active:
            return False
        if self.last_run_at is None:
            return True
        moment = now or _utcnow()
        return moment - self.last_run_at >= timedelta(minutes=self.interval_minutes)
