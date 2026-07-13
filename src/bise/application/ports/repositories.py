"""Repository ports (interfaces) owned by the application layer.

Concrete implementations live in ``infrastructure/db/repositories``. Business
logic depends only on these abstractions (Dependency Inversion), which is what
makes persistence swappable and use cases unit-testable with in-memory fakes.
"""

from __future__ import annotations

from typing import Protocol

from bise.domain.entities.company import Company
from bise.shared.pagination import Page, PageRequest


class CompanyRepository(Protocol):
    """Persistence operations for the :class:`Company` aggregate."""

    def add(self, company: Company) -> Company:
        """Persist a new company and return it with its assigned id."""
        ...

    def get(self, company_id: int) -> Company | None:
        """Return the company with the given id, or ``None`` if absent."""
        ...

    def find_by_hostname(self, hostname: str) -> Company | None:
        """Return the company owning the given domain hostname, if any."""
        ...

    def list(self, page: PageRequest) -> Page[Company]:
        """Return a page of companies ordered by creation time (newest first)."""
        ...
