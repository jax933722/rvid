"""ORM model for the denormalized search projection."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from bise.infrastructure.db.base import Base, TimestampMixin


class SearchDocumentModel(TimestampMixin, Base):
    """``search_documents`` table — one searchable row per company."""

    __tablename__ = "search_documents"
    # Composite indexes matching the common Sales-Navigator filter combinations
    # (industry + SEO-score range, grade + score). Single-column indexes below
    # still serve queries that use only one facet.
    __table_args__ = (
        Index("ix_search_industry_score", "industry", "seo_score"),
        Index("ix_search_grade_score", "seo_grade", "seo_score"),
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    primary_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    industry: Mapped[str | None] = mapped_column(String(128), index=True)
    country: Mapped[str | None] = mapped_column(String(128), index=True)
    state: Mapped[str | None] = mapped_column(String(128), index=True)
    city: Mapped[str | None] = mapped_column(String(128), index=True)
    size_bucket: Mapped[str | None] = mapped_column(String(32), index=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, index=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, index=True)
    seo_score: Mapped[float | None] = mapped_column(Float, index=True)
    seo_grade: Mapped[str | None] = mapped_column(String(1), index=True)
    technologies: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # Pipe-delimited lowercased names (e.g. "|wordpress|shopify|") for portable
    # CONTAINS matching via LIKE across SQLite and PostgreSQL.
    technologies_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    has_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    has_contact_page: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_careers_page: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_blog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_privacy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_terms: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    text_blob: Mapped[str] = mapped_column(Text, nullable=False, default="")
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
