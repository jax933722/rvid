"""``MarketingSignal`` entity — a marketing/advertising tool detected on a site."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class MarketingSignal:
    """A single marketing tool detected on a company's website, with evidence."""

    company_id: int
    tool_name: str
    category: str
    evidence: str
    id: int | None = field(default=None)
    detected_at: datetime = field(default_factory=_utcnow)
