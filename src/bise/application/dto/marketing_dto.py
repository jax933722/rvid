"""DTOs for marketing detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class MarketingSignalDTO:
    """A marketing tool detected on a company's website."""

    tool_name: str
    category: str
    evidence: str
    detected_at: datetime
