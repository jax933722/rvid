"""DTOs for business discovery."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiscoverCommand:
    """Input: what businesses to discover and where."""

    category: str
    location: str
    limit: int = 50


@dataclass(frozen=True, slots=True)
class DiscoveredBusinessDTO:
    """Output: a discovered business, with the saved company id if persisted."""

    name: str
    category: str
    website: str | None
    website_url: str | None
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    country: str | None
    postal_code: str | None
    latitude: float | None
    longitude: float | None
    source_url: str | None
    company_id: int | None  # set when saved as a company (had a website)
