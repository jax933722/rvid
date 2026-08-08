"""``Company`` aggregate root.

A company is the central business entity. It owns its website domains (the
aggregate boundary) and enforces the invariant that an *enriched/searchable*
company must have at least one domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from bise.domain.entities.website_domain import WebsiteDomain
from bise.domain.errors import InvalidValueError, InvariantViolationError


class CompanyStatus(StrEnum):
    """Pipeline lifecycle of a company record."""

    DISCOVERED = "discovered"
    CRAWLING = "crawling"
    ENRICHED = "enriched"
    ARCHIVED = "archived"


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Company:
    """Aggregate root representing a discovered business."""

    display_name: str
    legal_name: str | None = None
    status: CompanyStatus = CompanyStatus.DISCOVERED
    industry: str | None = None
    size_bucket: str | None = None
    # Firmographics — sourced only from public/open data (OpenStreetMap, the
    # company's own website). Fields we cannot source for free stay ``None``.
    country: str | None = None
    state: str | None = None
    city: str | None = None
    founded_year: int | None = None
    employee_count: int | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    domains: list[WebsiteDomain] = field(default_factory=list)
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.display_name or not self.display_name.strip():
            raise InvalidValueError("Company.display_name must be a non-empty string")
        self.display_name = self.display_name.strip()
        if self.founded_year is not None and not (1800 <= self.founded_year <= _utcnow().year + 1):
            raise InvalidValueError(
                f"Company.founded_year out of range (1800..{_utcnow().year + 1}): "
                f"{self.founded_year}"
            )
        if self.employee_count is not None and self.employee_count < 0:
            raise InvalidValueError("Company.employee_count must be non-negative")

    def add_domain(self, domain: WebsiteDomain) -> None:
        """Attach a website domain, enforcing hostname uniqueness and a single primary."""
        if any(d.hostname == domain.hostname for d in self.domains):
            raise InvariantViolationError(f"Domain already attached: {domain.hostname}")
        if domain.is_primary and any(d.is_primary for d in self.domains):
            raise InvariantViolationError("Company may have only one primary domain")
        if not self.domains and not domain.is_primary:
            domain.is_primary = True
        self.domains.append(domain)
        self._touch()

    @property
    def primary_domain(self) -> WebsiteDomain | None:
        """The primary domain, if any is attached."""
        return next((d for d in self.domains if d.is_primary), None)

    def mark_enriched(self) -> None:
        """Transition to ENRICHED; requires at least one domain (searchability invariant)."""
        if not self.domains:
            raise InvariantViolationError("A company must have at least one domain to be enriched")
        self.status = CompanyStatus.ENRICHED
        self._touch()

    def _touch(self) -> None:
        self.updated_at = _utcnow()
