"""ORM model for SEO profiles."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from bise.infrastructure.db.base import Base, TimestampMixin


class SeoProfileModel(TimestampMixin, Base):
    """``seo_profiles`` table — one current SEO profile per company."""

    __tablename__ = "seo_profiles"
    __table_args__ = (UniqueConstraint("company_id", name="uq_seo_profile_company"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str | None] = mapped_column(String(1024))
    meta_description: Mapped[str | None] = mapped_column(Text)
    canonical: Mapped[str | None] = mapped_column(String(2048))
    meta_robots: Mapped[str | None] = mapped_column(String(256))
    h1_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    h2_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_open_graph: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_twitter_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_structured_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    images_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    images_missing_alt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    internal_links: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    external_links: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    grade: Mapped[str] = mapped_column(String(1), nullable=False, index=True)
    cwv_lcp_ms: Mapped[int | None] = mapped_column(Integer)
    cwv_cls: Mapped[float | None] = mapped_column(Float)
    cwv_inp_ms: Mapped[int | None] = mapped_column(Integer)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
