"""ORM models for the lead engine (``lead_campaigns``, ``leads``)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from bise.infrastructure.db.base import Base, TimestampMixin


class LeadCampaignModel(TimestampMixin, Base):
    """``lead_campaigns`` table — a standing ICP that discovers on a schedule."""

    __tablename__ = "lead_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    locations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    auto_enrich: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    per_run_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    cursor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeadModel(TimestampMixin, Base):
    """``leads`` table — a company surfaced by a campaign (one per pair)."""

    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("campaign_id", "company_id", name="uq_lead_campaign_company"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("lead_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="new", index=True)
