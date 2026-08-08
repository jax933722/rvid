"""ORM models for workspaces and API keys."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from bise.infrastructure.db.base import Base, TimestampMixin


class WorkspaceModel(TimestampMixin, Base):
    """``workspaces`` table — a tenant boundary."""

    __tablename__ = "workspaces"
    __table_args__ = (UniqueConstraint("slug", name="uq_workspaces_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)


class ApiKeyModel(TimestampMixin, Base):
    """``api_keys`` table — a hashed credential scoped to a workspace."""

    __tablename__ = "api_keys"
    __table_args__ = (UniqueConstraint("key_hash", name="uq_api_keys_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
