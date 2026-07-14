"""Data Transfer Objects for the Company use cases.

DTOs are the stable boundary contract. Domain entities never cross the
application boundary directly, so persistence/domain internals can change
without breaking callers (API, workers, CLI).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NewDomainDTO:
    """Input: a website domain to attach to a new company."""

    hostname: str
    is_primary: bool = False


@dataclass(frozen=True, slots=True)
class CreateCompanyCommand:
    """Input command to create a company."""

    display_name: str
    legal_name: str | None = None
    industry: str | None = None
    size_bucket: str | None = None
    domains: tuple[NewDomainDTO, ...] = ()


@dataclass(frozen=True, slots=True)
class DomainDTO:
    """Output: a persisted website domain."""

    id: int | None
    hostname: str
    is_primary: bool
    crawl_status: str


@dataclass(frozen=True, slots=True)
class CompanyDTO:
    """Output: a company summary/detail view."""

    id: int | None
    display_name: str
    legal_name: str | None
    status: str
    industry: str | None
    size_bucket: str | None
    country: str | None
    state: str | None
    city: str | None
    founded_year: int | None
    employee_count: int | None
    contact_email: str | None
    contact_phone: str | None
    domains: tuple[DomainDTO, ...]
    created_at: datetime
    updated_at: datetime
