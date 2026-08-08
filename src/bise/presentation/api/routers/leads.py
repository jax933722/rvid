"""Lead engine API — recurring campaigns and the resulting lead inbox.

Campaigns are shared (not workspace-scoped): they describe *what businesses*
to keep discovering, and the leads they surface are the same public companies
everyone can search. Run them on a schedule via ``scripts/lead_engine.py`` or
kick a single cycle with ``POST /lead-campaigns/{id}/run``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from bise.application.use_cases.leads.list_leads import ListLeads
from bise.application.use_cases.leads.manage_campaigns import (
    CreateLeadCampaign,
    DeleteLeadCampaign,
    ListLeadCampaigns,
)
from bise.application.use_cases.leads.run_lead_campaign import RunLeadCampaign
from bise.presentation.api.dependencies import (
    ContainerDep,
    get_create_lead_campaign,
    get_delete_lead_campaign,
    get_list_lead_campaigns,
    get_list_leads,
    get_run_lead_campaign,
)
from bise.presentation.api.schemas.leads import (
    CampaignResponse,
    CampaignRunResponse,
    CreateCampaignRequest,
    LeadResponse,
)
from bise.presentation.workers.lead_engine import run_due_campaigns

router = APIRouter(tags=["leads"])


@router.post(
    "/lead-campaigns",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a recurring lead campaign (ICP)",
)
async def create_campaign(
    body: CreateCampaignRequest,
    use_case: Annotated[CreateLeadCampaign, Depends(get_create_lead_campaign)],
) -> CampaignResponse:
    return CampaignResponse.from_dto(use_case.execute(body.to_command()))


@router.get(
    "/lead-campaigns",
    response_model=list[CampaignResponse],
    summary="List campaigns with progress and lead counts",
)
async def list_campaigns(
    use_case: Annotated[ListLeadCampaigns, Depends(get_list_lead_campaigns)],
) -> list[CampaignResponse]:
    return [CampaignResponse.from_dto(c) for c in use_case.execute()]


@router.delete(
    "/lead-campaigns/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a campaign and its leads",
)
async def delete_campaign(
    campaign_id: int,
    use_case: Annotated[DeleteLeadCampaign, Depends(get_delete_lead_campaign)],
) -> None:
    if not use_case.execute(campaign_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign not found: {campaign_id}",
        )


@router.post(
    "/lead-campaigns/{campaign_id}/run",
    response_model=CampaignRunResponse,
    summary="Run one rotation step of a campaign now",
)
async def run_campaign(
    campaign_id: int,
    use_case: Annotated[RunLeadCampaign, Depends(get_run_lead_campaign)],
) -> CampaignRunResponse:
    """Discover the next grid cell, record net-new leads, advance the cursor."""
    return CampaignRunResponse.from_dto(use_case.execute(campaign_id))


@router.post(
    "/lead-campaigns/run-due",
    summary="Run every campaign that is currently due",
)
async def run_due(container: ContainerDep) -> dict[str, int]:
    """Run all due campaigns once and report how many net-new leads were found.

    For hands-off operation, run ``scripts/lead_engine.py`` as a separate
    process against the same database instead.
    """
    new_leads = run_due_campaigns(container)
    return {"new_leads": new_leads}


@router.get(
    "/leads",
    response_model=list[LeadResponse],
    summary="Lead inbox — freshest leads first",
)
async def list_leads(
    use_case: Annotated[ListLeads, Depends(get_list_leads)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    campaign_id: Annotated[int | None, Query()] = None,
) -> list[LeadResponse]:
    return [LeadResponse.from_dto(lead) for lead in use_case.execute(limit, campaign_id)]
