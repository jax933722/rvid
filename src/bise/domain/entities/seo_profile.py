"""``SeoProfile`` entity — a company's SEO scan result."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from bise.domain.value_objects.seo_grade import SeoGrade
from bise.domain.value_objects.seo_signals import SeoSignals


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class SeoProfile:
    """The scored SEO profile for a company's website."""

    company_id: int
    signals: SeoSignals
    score: float
    # Optional Core Web Vitals (populated by a pluggable provider; may be absent).
    cwv_lcp_ms: int | None = None
    cwv_cls: float | None = None
    cwv_inp_ms: int | None = None
    id: int | None = field(default=None)
    scanned_at: datetime = field(default_factory=_utcnow)

    @property
    def grade(self) -> str:
        """The letter grade derived from the numeric score."""
        return str(SeoGrade(self.score))
