"""Use cases for managing lead campaigns: create, list, delete."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.lead_dto import CreateLeadCampaignCommand, LeadCampaignDTO
from bise.application.mappers import lead_campaign_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.lead_campaign import LeadCampaign

logger = get_logger(__name__)


class CreateLeadCampaign:
    """Define a new recurring campaign from an ideal-customer profile."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: CreateLeadCampaignCommand) -> LeadCampaignDTO:
        campaign = LeadCampaign(
            name=command.name,
            categories=list(command.categories),
            locations=list(command.locations),
            interval_minutes=command.interval_minutes,
            auto_enrich=command.auto_enrich,
            per_run_limit=command.per_run_limit,
        )
        with self._uow as uow:
            saved = uow.lead_campaigns.add(campaign)
            uow.commit()
        logger.info("lead_campaign.created", campaign_id=saved.id, name=saved.name)
        return lead_campaign_to_dto(saved, lead_count=0)


class ListLeadCampaigns:
    """List every campaign with its current progress and lead count."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self) -> list[LeadCampaignDTO]:
        with self._uow as uow:
            campaigns = uow.lead_campaigns.list()
            result: list[LeadCampaignDTO] = []
            for campaign in campaigns:
                assert campaign.id is not None
                count = uow.leads.count_for_campaign(campaign.id)
                result.append(lead_campaign_to_dto(campaign, lead_count=count))
        return result


class DeleteLeadCampaign:
    """Delete a campaign (and, by cascade, its leads)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, campaign_id: int) -> bool:
        with self._uow as uow:
            deleted = uow.lead_campaigns.delete(campaign_id)
            uow.commit()
        logger.info("lead_campaign.deleted", campaign_id=campaign_id, deleted=deleted)
        return deleted
