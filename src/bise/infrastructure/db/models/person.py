"""ORM model for people extracted from company websites (``people``)."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from bise.infrastructure.db.base import Base, TimestampMixin


class PersonModel(TimestampMixin, Base):
    """``people`` table — one team member published on a company's site."""

    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    role_category: Mapped[str] = mapped_column(
        String(32), nullable=False, default="other", index=True
    )
    email: Mapped[str | None] = mapped_column(String(320))
    email_status: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    source_url: Mapped[str | None] = mapped_column(String(2048))
