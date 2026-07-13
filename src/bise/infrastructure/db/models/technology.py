"""ORM models for technology reference data and detections."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bise.infrastructure.db.base import Base, TimestampMixin


class TechnologyCategoryModel(TimestampMixin, Base):
    """``technology_categories`` table — groups technologies (CMS, Analytics…)."""

    __tablename__ = "technology_categories"
    __table_args__ = (UniqueConstraint("name", name="uq_tech_category_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


class TechnologyModel(TimestampMixin, Base):
    """``technologies`` table — canonical technologies (shared reference data)."""

    __tablename__ = "technologies"
    __table_args__ = (UniqueConstraint("name", name="uq_technology_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(128))
    category_id: Mapped[int] = mapped_column(
        ForeignKey("technology_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    category: Mapped[TechnologyCategoryModel] = relationship(lazy="joined")


class CompanyTechnologyModel(TimestampMixin, Base):
    """``company_technologies`` table — a detected technology on a company."""

    __tablename__ = "company_technologies"
    __table_args__ = (
        UniqueConstraint("company_id", "technology_id", name="uq_company_technology"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    technology_id: Mapped[int] = mapped_column(
        ForeignKey("technologies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(String(64))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    technology: Mapped[TechnologyModel] = relationship(lazy="joined")
