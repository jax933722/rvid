"""Request/response schemas for the lead engine (campaigns + lead inbox)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from bise.application.dto.lead_dto import (
    CampaignRunResultDTO,
    CreateLeadCampaignCommand,
    LeadCampaignDTO,
    LeadDTO,
)
from bise.presentation.api.schemas.company import CompanyResponse


class CreateCampaignRequest(BaseModel):
    """Request body for ``POST /lead-campaigns``."""

    name: str = Field(min_length=1, max_length=200)
    categories: list[str] = Field(min_length=1, description="Business categories to sweep")
    locations: list[str] = Field(min_length=1, description="Locations to sweep")
    interval_minutes: int = Field(default=60, ge=1)
    auto_enrich: bool = True
    per_run_limit: int = Field(default=50, ge=1, le=200)

    def to_command(self) -> CreateLeadCampaignCommand:
        return CreateLeadCampaignCommand(
            name=self.name,
            categories=tuple(self.categories),
            locations=tuple(self.locations),
            interval_minutes=self.interval_minutes,
            auto_enrich=self.auto_enrich,
            per_run_limit=self.per_run_limit,
        )


class CampaignResponse(BaseModel):
    """A campaign with its rotation progress and lead count."""

    id: int | None
    name: str
    categories: list[str]
    locations: list[str]
    interval_minutes: int
    is_active: bool
    auto_enrich: bool
    per_run_limit: int
    lead_count: int
    grid_size: int
    next_category: str
    next_location: str
    last_run_at: datetime | None
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: LeadCampaignDTO) -> CampaignResponse:
        next_category, next_location = dto.next_target
        return cls(
            id=dto.id,
            name=dto.name,
            categories=list(dto.categories),
            locations=list(dto.locations),
            interval_minutes=dto.interval_minutes,
            is_active=dto.is_active,
            auto_enrich=dto.auto_enrich,
            per_run_limit=dto.per_run_limit,
            lead_count=dto.lead_count,
            grid_size=dto.grid_size,
            next_category=next_category,
            next_location=next_location,
            last_run_at=dto.last_run_at,
            created_at=dto.created_at,
        )


class CampaignRunResponse(BaseModel):
    """What a single campaign run produced."""

    campaign_id: int
    category: str
    location: str
    found: int
    new_leads: int
    enqueued_enrichment: int

    @classmethod
    def from_dto(cls, dto: CampaignRunResultDTO) -> CampaignRunResponse:
        return cls(
            campaign_id=dto.campaign_id,
            category=dto.category,
            location=dto.location,
            found=dto.found,
            new_leads=dto.new_leads,
            enqueued_enrichment=dto.enqueued_enrichment,
        )


class LeadResponse(BaseModel):
    """A lead: its company plus pipeline status."""

    id: int | None
    campaign_id: int
    status: str
    created_at: datetime
    company: CompanyResponse

    @classmethod
    def from_dto(cls, dto: LeadDTO) -> LeadResponse:
        return cls(
            id=dto.id,
            campaign_id=dto.campaign_id,
            status=dto.status,
            created_at=dto.created_at,
            company=CompanyResponse.from_dto(dto.company),
        )
