"""Request/response schemas for the workspace API (saved searches, lists, tags)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from bise.application.dto.workspace_dto import (
    CompanyListDTO,
    CompanyTagDTO,
    SavedSearchDTO,
)


class SaveSearchRequest(BaseModel):
    """Request body for ``POST /saved-searches``."""

    name: str = Field(..., min_length=1, examples=["Sydney dentists on WordPress"])
    # The Prospector query payload, stored verbatim and replayed on apply.
    query: dict[str, Any] = Field(..., description="The SearchRequest payload to persist")


class SavedSearchResponse(BaseModel):
    """A persisted saved search."""

    id: int | None
    name: str
    query: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: SavedSearchDTO) -> SavedSearchResponse:
        return cls(
            id=dto.id,
            name=dto.name,
            query=json.loads(dto.query_json),
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class CreateListRequest(BaseModel):
    """Request body for ``POST /lists``."""

    name: str = Field(..., min_length=1, examples=["Q3 outreach"])
    description: str | None = Field(default=None, examples=["Warm dentistry leads"])


class AddToListRequest(BaseModel):
    """Request body for ``POST /lists/{id}/companies``."""

    company_id: int = Field(..., examples=[1])


class CompanyListResponse(BaseModel):
    """A company list with its current member count."""

    id: int | None
    name: str
    description: str | None
    member_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: CompanyListDTO) -> CompanyListResponse:
        return cls(
            id=dto.id,
            name=dto.name,
            description=dto.description,
            member_count=dto.member_count,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class AddTagRequest(BaseModel):
    """Request body for ``POST /companies/{id}/tags``."""

    label: str = Field(..., min_length=1, examples=["priority"])


class CompanyTagResponse(BaseModel):
    """A tag on a company."""

    id: int | None
    company_id: int
    label: str
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: CompanyTagDTO) -> CompanyTagResponse:
        return cls(
            id=dto.id,
            company_id=dto.company_id,
            label=dto.label,
            created_at=dto.created_at,
        )
