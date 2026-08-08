"""DTO for people extracted from company websites."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PersonDTO:
    """Output: a person listed on a company's public site."""

    id: int | None
    company_id: int
    name: str
    title: str | None
    role_category: str
    email: str | None
    email_status: str
    source_url: str | None
