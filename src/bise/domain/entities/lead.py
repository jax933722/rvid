"""``Lead`` — a company surfaced by a campaign, tracked through your pipeline.

A lead is the join between a campaign and a discovered company. It is created
once per (campaign, company) so a business you've already seen never shows up as
a "new" lead again, and it carries a light pipeline status you can advance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class LeadStatus(StrEnum):
    """Where a lead sits in your outreach pipeline."""

    NEW = "new"
    ENRICHING = "enriching"
    READY = "ready"
    CONTACTED = "contacted"
    ARCHIVED = "archived"


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Lead:
    """A company brought in by a campaign."""

    campaign_id: int
    company_id: int
    status: LeadStatus = LeadStatus.NEW
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)
