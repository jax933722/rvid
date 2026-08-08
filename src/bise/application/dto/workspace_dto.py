"""Data Transfer Objects for workspace features (saved searches, lists, tags)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SavedSearchDTO:
    """Output: a persisted saved Prospector search."""

    id: int | None
    name: str
    query_json: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CompanyListDTO:
    """Output: a company list with its current member count."""

    id: int | None
    name: str
    description: str | None
    member_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CompanyTagDTO:
    """Output: a tag applied to a company."""

    id: int | None
    company_id: int
    label: str
    created_at: datetime
