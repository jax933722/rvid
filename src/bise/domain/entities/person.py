"""``Person`` — a team member published on a company's own website.

People are extracted only from what a company publishes about itself (team /
about / leadership pages) — public information, never scraped from LinkedIn or a
paid dataset. Emails are either published on the site (``PUBLISHED``) or inferred
from an email pattern observed on that same domain (``GUESSED``); the latter is
clearly labelled as unverified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from bise.domain.errors import InvalidValueError


class RoleCategory(StrEnum):
    """Normalized seniority/role bucket derived from a person's title."""

    FOUNDER = "founder"
    CEO = "ceo"
    CTO = "cto"
    CFO = "cfo"
    COO = "coo"
    CMO = "cmo"
    VP = "vp"
    DIRECTOR = "director"
    HEAD = "head"
    MANAGER = "manager"
    OTHER = "other"


class EmailStatus(StrEnum):
    """Provenance of a person's email address."""

    NONE = "none"
    PUBLISHED = "published"  # found verbatim on the company's site
    GUESSED = "guessed"  # inferred from a pattern seen on the same domain


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Person:
    """A person listed on a company's public website."""

    company_id: int
    name: str
    title: str | None = None
    role_category: RoleCategory = RoleCategory.OTHER
    email: str | None = None
    email_status: EmailStatus = EmailStatus.NONE
    source_url: str | None = None
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidValueError("Person.name must be a non-empty string")
        self.name = " ".join(self.name.split())
        if self.title is not None:
            self.title = self.title.strip() or None
        if self.email is not None:
            self.email = self.email.strip().lower() or None
        if self.email is None:
            self.email_status = EmailStatus.NONE
