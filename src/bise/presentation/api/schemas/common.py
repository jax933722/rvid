"""Shared API schemas (pagination envelope, error problem details)."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """A paginated list response."""

    items: list[T]
    total: int = Field(..., description="Total number of matching records.")
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)


class ProblemDetail(BaseModel):
    """RFC 7807-style error response body."""

    title: str
    status: int
    detail: str
    correlation_id: str | None = None
