"""DTOs for technology detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TechnologyDTO:
    """A canonical technology reference entry."""

    id: int | None
    name: str
    category: str
    vendor: str | None


@dataclass(frozen=True, slots=True)
class CompanyTechnologyDTO:
    """A technology detected on a company's website, with evidence."""

    name: str
    category: str
    confidence: float
    evidence: str
    version: str | None
    detected_at: datetime
