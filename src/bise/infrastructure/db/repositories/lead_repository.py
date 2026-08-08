"""SQLAlchemy implementations of the lead-campaign and lead repositories."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bise.domain.entities.company import Company
from bise.domain.entities.lead import Lead, LeadStatus
from bise.domain.entities.lead_campaign import LeadCampaign
from bise.infrastructure.db.models.company import CompanyModel
from bise.infrastructure.db.models.lead import LeadCampaignModel, LeadModel
from bise.infrastructure.db.repositories.company_repository import _to_entity as _company_to_entity


def _aware(value: datetime | None) -> datetime | None:
    """Treat a stored datetime as UTC (SQLite drops tzinfo on round-trip)."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _campaign_to_entity(model: LeadCampaignModel) -> LeadCampaign:
    created = _aware(model.created_at)
    updated = _aware(model.updated_at)
    campaign = LeadCampaign(
        id=model.id,
        name=model.name,
        categories=list(model.categories or []),
        locations=list(model.locations or []),
        interval_minutes=model.interval_minutes,
        is_active=model.is_active,
        auto_enrich=model.auto_enrich,
        per_run_limit=model.per_run_limit,
        cursor=model.cursor,
        last_run_at=_aware(model.last_run_at),
    )
    if created is not None:
        campaign.created_at = created
    if updated is not None:
        campaign.updated_at = updated
    return campaign


def _lead_to_entity(model: LeadModel) -> Lead:
    return Lead(
        id=model.id,
        campaign_id=model.campaign_id,
        company_id=model.company_id,
        status=LeadStatus(model.status),
        created_at=model.created_at,
    )


class SqlAlchemyLeadCampaignRepository:
    """Lead-campaign persistence backed by a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, campaign: LeadCampaign) -> LeadCampaign:
        model = LeadCampaignModel(
            name=campaign.name,
            categories=campaign.categories,
            locations=campaign.locations,
            interval_minutes=campaign.interval_minutes,
            is_active=campaign.is_active,
            auto_enrich=campaign.auto_enrich,
            per_run_limit=campaign.per_run_limit,
            cursor=campaign.cursor,
            last_run_at=campaign.last_run_at,
        )
        self._session.add(model)
        self._session.flush()
        return _campaign_to_entity(model)

    def get(self, campaign_id: int) -> LeadCampaign | None:
        model = self._session.get(LeadCampaignModel, campaign_id)
        return _campaign_to_entity(model) if model is not None else None

    def update(self, campaign: LeadCampaign) -> None:
        assert campaign.id is not None, "cannot update an unsaved campaign"
        model = self._session.get(LeadCampaignModel, campaign.id)
        if model is None:
            raise KeyError(f"LeadCampaign not found: {campaign.id}")
        model.name = campaign.name
        model.categories = campaign.categories
        model.locations = campaign.locations
        model.interval_minutes = campaign.interval_minutes
        model.is_active = campaign.is_active
        model.auto_enrich = campaign.auto_enrich
        model.per_run_limit = campaign.per_run_limit
        model.cursor = campaign.cursor
        model.last_run_at = campaign.last_run_at
        self._session.flush()

    def list(self) -> Sequence[LeadCampaign]:
        stmt = select(LeadCampaignModel).order_by(
            LeadCampaignModel.created_at.desc(), LeadCampaignModel.id.desc()
        )
        return [_campaign_to_entity(m) for m in self._session.scalars(stmt).all()]

    def list_due(self, now: datetime) -> Sequence[LeadCampaign]:
        stmt = select(LeadCampaignModel).where(LeadCampaignModel.is_active.is_(True))
        campaigns = [_campaign_to_entity(m) for m in self._session.scalars(stmt).all()]
        return [c for c in campaigns if c.is_due(now)]

    def delete(self, campaign_id: int) -> bool:
        model = self._session.get(LeadCampaignModel, campaign_id)
        if model is None:
            return False
        self._session.delete(model)  # cascade removes leads
        self._session.flush()
        return True


class SqlAlchemyLeadRepository:
    """Lead persistence + dedup + inbox reads."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def exists(self, campaign_id: int, company_id: int) -> bool:
        found = self._session.scalar(
            select(LeadModel.id).where(
                LeadModel.campaign_id == campaign_id,
                LeadModel.company_id == company_id,
            )
        )
        return found is not None

    def add(self, lead: Lead) -> Lead:
        model = LeadModel(
            campaign_id=lead.campaign_id,
            company_id=lead.company_id,
            status=lead.status.value,
        )
        self._session.add(model)
        self._session.flush()
        return _lead_to_entity(model)

    def count_for_campaign(self, campaign_id: int) -> int:
        return (
            self._session.scalar(
                select(func.count())
                .select_from(LeadModel)
                .where(LeadModel.campaign_id == campaign_id)
            )
            or 0
        )

    def list_recent(
        self, limit: int, campaign_id: int | None = None
    ) -> Sequence[tuple[Lead, Company]]:
        stmt = (
            select(LeadModel, CompanyModel)
            .join(CompanyModel, CompanyModel.id == LeadModel.company_id)
            .order_by(LeadModel.created_at.desc(), LeadModel.id.desc())
            .limit(limit)
        )
        if campaign_id is not None:
            stmt = stmt.where(LeadModel.campaign_id == campaign_id)
        rows = self._session.execute(stmt).all()
        return [(_lead_to_entity(lead), _company_to_entity(company)) for lead, company in rows]
