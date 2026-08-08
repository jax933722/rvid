"""Use case: run one campaign cycle — the heartbeat of continuous lead flow.

A run discovers businesses at the campaign's *current* grid cell, records only
the companies it has never surfaced for this campaign as fresh leads (dedup),
optionally queues them for enrichment, then advances the rotation cursor so the
next run sweeps a different cell. Repeated on a schedule, this keeps bringing in
net-new leads without any paid API.
"""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.discovery_dto import DiscoverCommand
from bise.application.dto.lead_dto import CampaignRunResultDTO
from bise.application.errors import NotFoundError
from bise.application.ports.discovery import DiscoverySourcePort
from bise.application.ports.unit_of_work import UnitOfWork
from bise.application.use_cases.discovery.discover_businesses import DiscoverBusinesses
from bise.domain.entities.enrichment_job import EnrichmentJob
from bise.domain.entities.lead import Lead

logger = get_logger(__name__)


class RunLeadCampaign:
    """Execute a single rotation step of a campaign and record fresh leads."""

    def __init__(self, uow: UnitOfWork, source: DiscoverySourcePort) -> None:
        self._uow = uow
        self._source = source

    def execute(self, campaign_id: int) -> CampaignRunResultDTO:
        with self._uow as uow:
            campaign = uow.lead_campaigns.get(campaign_id)
            if campaign is None:
                raise NotFoundError(f"LeadCampaign not found: {campaign_id}")
            category, location = campaign.current_target()
            auto_enrich = campaign.auto_enrich
            per_run_limit = campaign.per_run_limit

        # Discovery persists net-new companies in its own transaction and returns
        # each business tagged with its company_id (None if it had no website).
        discovered = DiscoverBusinesses(self._uow, self._source).execute(
            DiscoverCommand(category=category, location=location, limit=per_run_limit)
        )

        new_leads = 0
        enqueued = 0
        with self._uow as uow:
            campaign = uow.lead_campaigns.get(campaign_id)
            if campaign is None:  # deleted mid-run
                raise NotFoundError(f"LeadCampaign not found: {campaign_id}")
            for biz in discovered:
                if biz.company_id is None:
                    continue
                if uow.leads.exists(campaign_id, biz.company_id):
                    continue
                uow.leads.add(Lead(campaign_id=campaign_id, company_id=biz.company_id))
                new_leads += 1
                if auto_enrich and not uow.enrichment_jobs.has_active_for_company(biz.company_id):
                    uow.enrichment_jobs.add(EnrichmentJob(company_id=biz.company_id))
                    enqueued += 1
            campaign.advance()
            uow.lead_campaigns.update(campaign)
            uow.commit()

        logger.info(
            "lead_campaign.run",
            campaign_id=campaign_id,
            category=category,
            location=location,
            found=len(discovered),
            new_leads=new_leads,
            enqueued_enrichment=enqueued,
        )
        return CampaignRunResultDTO(
            campaign_id=campaign_id,
            category=category,
            location=location,
            found=len(discovered),
            new_leads=new_leads,
            enqueued_enrichment=enqueued,
        )
