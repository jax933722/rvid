"""Request/response schemas for the technology API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from bise.application.dto.technology_dto import CompanyTechnologyDTO, TechnologyDTO


class TechnologyResponse(BaseModel):
    """A known technology in the catalog."""

    id: int | None
    name: str
    category: str
    vendor: str | None

    @classmethod
    def from_dto(cls, dto: TechnologyDTO) -> TechnologyResponse:
        return cls(id=dto.id, name=dto.name, category=dto.category, vendor=dto.vendor)


class CompanyTechnologyResponse(BaseModel):
    """A technology detected on a company's website."""

    name: str
    category: str
    confidence: float
    evidence: str
    version: str | None
    detected_at: datetime

    @classmethod
    def from_dto(cls, dto: CompanyTechnologyDTO) -> CompanyTechnologyResponse:
        return cls(
            name=dto.name,
            category=dto.category,
            confidence=dto.confidence,
            evidence=dto.evidence,
            version=dto.version,
            detected_at=dto.detected_at,
        )
