"""Request/response schemas for the discovery API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from bise.application.dto.discovery_dto import DiscoverCommand, DiscoveredBusinessDTO


class DiscoverRequest(BaseModel):
    """Request body for ``POST /discover``."""

    category: str = Field(
        ..., examples=["dentist"], description="Business type, e.g. dentist, cafe"
    )
    location: str = Field(..., examples=["Sydney, Australia"])
    limit: int = Field(default=50, ge=1, le=200)

    def to_command(self) -> DiscoverCommand:
        return DiscoverCommand(category=self.category, location=self.location, limit=self.limit)


class DiscoveredBusinessResponse(BaseModel):
    """A discovered business."""

    name: str
    category: str
    website: str | None
    website_url: str | None
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    country: str | None
    postal_code: str | None
    latitude: float | None
    longitude: float | None
    source_url: str | None
    company_id: int | None

    @classmethod
    def from_dto(cls, dto: DiscoveredBusinessDTO) -> DiscoveredBusinessResponse:
        return cls(
            name=dto.name,
            category=dto.category,
            website=dto.website,
            website_url=dto.website_url,
            phone=dto.phone,
            address=dto.address,
            city=dto.city,
            state=dto.state,
            country=dto.country,
            postal_code=dto.postal_code,
            latitude=dto.latitude,
            longitude=dto.longitude,
            source_url=dto.source_url,
            company_id=dto.company_id,
        )
