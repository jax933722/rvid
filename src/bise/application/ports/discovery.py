"""Business discovery port.

Given search criteria (a business category + a location), a discovery source
returns candidate businesses from a public dataset. The default implementation
uses OpenStreetMap (Nominatim + Overpass) — free, open, no API key, no LinkedIn.
A different source is a drop-in replacement behind this interface.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DiscoveryCriteria:
    """What to look for and where."""

    category: str  # e.g. "dentist", "cafe", "plumber"
    location: str  # e.g. "Sydney, Australia"
    limit: int = 50


@dataclass(frozen=True, slots=True)
class DiscoveredBusiness:
    """A business found in a public dataset (not yet crawled/enriched)."""

    name: str
    category: str
    website: str | None = None  # normalized hostname, e.g. "acme.com"
    website_url: str | None = None  # the raw URL as published
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    source_url: str | None = None  # link back to the source record


class DiscoverySourcePort(Protocol):
    """Finds businesses matching criteria from a public source."""

    def discover(self, criteria: DiscoveryCriteria) -> Sequence[DiscoveredBusiness]:
        """Return businesses matching the criteria (may be empty)."""
        ...
