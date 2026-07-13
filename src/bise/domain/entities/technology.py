"""Technology entities.

``Technology`` is canonical reference data (shared across companies).
``CompanyTechnology`` is the evidence-bearing link between a company and a
technology detected on its website.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from bise.domain.value_objects.confidence import Confidence


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Technology:
    """A canonical technology (e.g. WordPress) in a category (e.g. CMS)."""

    name: str
    category: str
    vendor: str | None = None
    id: int | None = field(default=None)


@dataclass(slots=True)
class CompanyTechnology:
    """A technology detected on a company's website, with evidence."""

    company_id: int
    technology_id: int
    confidence: Confidence
    evidence: str
    version: str | None = None
    id: int | None = field(default=None)
    detected_at: datetime = field(default_factory=_utcnow)
    # Populated on reads for convenience (not persisted here).
    technology: Technology | None = None
