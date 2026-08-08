"""DTOs for the lead engine (campaigns, leads, run results)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from bise.application.dto.company_dto import CompanyDTO


@dataclass(frozen=True, slots=True)
class CreateLeadCampaignCommand:
    """Input: define a recurring lead campaign (ICP)."""

    name: str
    categories: tuple[str, ...]
    locations: tuple[str, ...]
    interval_minutes: int = 60
    auto_enrich: bool = True
    per_run_limit: int = 50


@dataclass(frozen=True, slots=True)
class LeadCampaignDTO:
    """Output: a campaign with its progress."""

    id: int | None
    name: str
    categories: tuple[str, ...]
    locations: tuple[str, ...]
    interval_minutes: int
    is_active: bool
    auto_enrich: bool
    per_run_limit: int
    lead_count: int
    grid_size: int
    next_target: tuple[str, str]
    last_run_at: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class LeadDTO:
    """Output: a lead (its company plus pipeline status)."""

    id: int | None
    campaign_id: int
    status: str
    created_at: datetime
    company: CompanyDTO


@dataclass(frozen=True, slots=True)
class CampaignRunResultDTO:
    """Output: what one campaign run produced."""

    campaign_id: int
    category: str
    location: str
    found: int
    new_leads: int
    enqueued_enrichment: int
