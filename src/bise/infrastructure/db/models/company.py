"""ORM models for the Company aggregate (persistence shape).

These are deliberately separate from the domain entities. Repositories map
between the two so the domain never depends on SQLAlchemy.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bise.infrastructure.db.base import Base, TimestampMixin


class CompanyModel(TimestampMixin, Base):
    """``companies`` table — the aggregate root."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    legal_name: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="discovered", index=True
    )
    industry: Mapped[str | None] = mapped_column(String(128), index=True)
    size_bucket: Mapped[str | None] = mapped_column(String(32), index=True)

    domains: Mapped[list[DomainModel]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DomainModel(TimestampMixin, Base):
    """``domains`` table — a website hostname owned by exactly one company."""

    __tablename__ = "domains"
    __table_args__ = (UniqueConstraint("hostname", name="uq_domains_hostname"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    crawl_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )

    company: Mapped[CompanyModel] = relationship(back_populates="domains")
