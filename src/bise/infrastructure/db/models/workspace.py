"""ORM models for workspace features: saved searches, lists, and tags."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bise.infrastructure.db.base import Base, TimestampMixin


class SavedSearchModel(TimestampMixin, Base):
    """``saved_searches`` table — a named Prospector query payload."""

    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    query_json: Mapped[str] = mapped_column(Text, nullable=False)


class CompanyListModel(TimestampMixin, Base):
    """``company_lists`` table — a named collection of companies."""

    __tablename__ = "company_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(512))

    items: Mapped[list[CompanyListItemModel]] = relationship(
        back_populates="list",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CompanyListItemModel(TimestampMixin, Base):
    """``company_list_items`` table — membership of a company in a list."""

    __tablename__ = "company_list_items"
    __table_args__ = (
        UniqueConstraint("list_id", "company_id", name="uq_list_company"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(
        ForeignKey("company_lists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    list: Mapped[CompanyListModel] = relationship(back_populates="items")


class CompanyTagModel(TimestampMixin, Base):
    """``company_tags`` table — a normalized label on a company."""

    __tablename__ = "company_tags"
    __table_args__ = (
        UniqueConstraint("workspace_id", "company_id", "label", name="uq_ws_company_label"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
