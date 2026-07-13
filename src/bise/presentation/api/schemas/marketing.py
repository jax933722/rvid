"""Response schema for the marketing API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from bise.application.dto.marketing_dto import MarketingSignalDTO


class MarketingSignalResponse(BaseModel):
    """A marketing tool detected on a company's website."""

    tool_name: str
    category: str
    evidence: str
    detected_at: datetime

    @classmethod
    def from_dto(cls, dto: MarketingSignalDTO) -> MarketingSignalResponse:
        return cls(
            tool_name=dto.tool_name,
            category=dto.category,
            evidence=dto.evidence,
            detected_at=dto.detected_at,
        )
