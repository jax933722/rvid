"""OpenStreetMap business discovery (Nominatim geocode + Overpass query).

Free and open — no API key, no paid API, no LinkedIn. Flow:
  1. Geocode the location to a bounding box via Nominatim.
  2. Query Overpass for businesses of the requested category in that box.
  3. Map OSM tags to :class:`DiscoveredBusiness`.

The HTTP client is injectable so the parsing/mapping is fully testable offline.
Per OSM usage policy, a descriptive User-Agent is sent and results are capped.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx
from config.logging import get_logger

from bise.application.ports.discovery import (
    DiscoveredBusiness,
    DiscoveryCriteria,
    DiscoverySourcePort,
)
from bise.domain.value_objects.url import Url

logger = get_logger(__name__)

# Map a free-text category to an Overpass tag filter. Unknown categories fall
# back to a name search within the area.
_CATEGORY_TAGS: dict[str, str] = {
    "dentist": "amenity=dentist",
    "doctor": "amenity=doctors",
    "clinic": "amenity=clinic",
    "cafe": "amenity=cafe",
    "coffee": "amenity=cafe",
    "restaurant": "amenity=restaurant",
    "bar": "amenity=bar",
    "pub": "amenity=pub",
    "pharmacy": "amenity=pharmacy",
    "veterinary": "amenity=veterinary",
    "vet": "amenity=veterinary",
    "plumber": "craft=plumber",
    "electrician": "craft=electrician",
    "builder": "craft=builder",
    "lawyer": "office=lawyer",
    "accountant": "office=accountant",
    "estate agent": "office=estate_agent",
    "real estate": "office=estate_agent",
    "gym": "leisure=fitness_centre",
    "fitness": "leisure=fitness_centre",
    "hairdresser": "shop=hairdresser",
    "salon": "shop=hairdresser",
    "barber": "shop=hairdresser",
    "bakery": "shop=bakery",
    "florist": "shop=florist",
    "car repair": "shop=car_repair",
    "mechanic": "shop=car_repair",
    "hotel": "tourism=hotel",
}


@dataclass(frozen=True, slots=True)
class OverpassConfig:
    """Endpoints and politeness settings."""

    nominatim_url: str = "https://nominatim.openstreetmap.org/search"
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    user_agent: str = "BISE/0.1 (business-intelligence-search-engine)"
    timeout_seconds: float = 30.0


def _category_filter(category: str) -> str:
    key = category.strip().lower()
    if key in _CATEGORY_TAGS:
        tag = _CATEGORY_TAGS[key]
        return f"[{tag}]"
    # Fallback: match the name (case-insensitive) — broader, still bounded by area.
    safe = category.replace('"', "").strip()
    return f'[name~"{safe}",i]'


class OverpassDiscoverySource(DiscoverySourcePort):
    """Discovers businesses from OpenStreetMap."""

    def __init__(
        self, config: OverpassConfig | None = None, client: httpx.Client | None = None
    ) -> None:
        self._config = config or OverpassConfig()
        self._client = client or httpx.Client(
            headers={"User-Agent": self._config.user_agent},
            timeout=self._config.timeout_seconds,
        )

    def discover(self, criteria: DiscoveryCriteria) -> Sequence[DiscoveredBusiness]:
        bbox = self._geocode(criteria.location)
        if bbox is None:
            logger.warning("discovery.location_not_found", location=criteria.location)
            return []
        elements = self._overpass(criteria.category, bbox, criteria.limit)
        results = [self._to_business(e, criteria.category) for e in elements]
        return [b for b in results if b is not None][: criteria.limit]

    # --- steps -------------------------------------------------------------
    def _geocode(self, location: str) -> tuple[float, float, float, float] | None:
        try:
            resp = self._client.get(
                self._config.nominatim_url,
                params={"format": "json", "limit": "1", "q": location},
            )
        except httpx.HTTPError as exc:
            logger.warning("discovery.geocode_error", error=type(exc).__name__)
            return None
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data:
            return None
        box = data[0].get("boundingbox")
        if not box or len(box) != 4:
            return None
        # Nominatim: [minlat, maxlat, minlon, maxlon]
        return (float(box[0]), float(box[1]), float(box[2]), float(box[3]))

    def _overpass(
        self, category: str, bbox: tuple[float, float, float, float], limit: int
    ) -> list[dict[str, Any]]:
        minlat, maxlat, minlon, maxlon = bbox
        tag = _category_filter(category)
        box = f"{minlat},{minlon},{maxlat},{maxlon}"
        query = (
            f"[out:json][timeout:25];"
            f"(node{tag}({box});way{tag}({box}););"
            f"out center tags {max(1, min(limit, 200))};"
        )
        try:
            resp = self._client.post(self._config.overpass_url, data={"data": query})
        except httpx.HTTPError as exc:
            logger.warning("discovery.overpass_error", error=type(exc).__name__)
            return []
        if resp.status_code != 200:
            return []
        elements = resp.json().get("elements", [])
        return [e for e in elements if isinstance(e, dict)]

    # --- mapping -----------------------------------------------------------
    @staticmethod
    def _to_business(element: dict[str, Any], category: str) -> DiscoveredBusiness | None:
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            return None

        website_url = tags.get("website") or tags.get("contact:website")
        hostname: str | None = None
        if website_url:
            candidate = website_url if "://" in website_url else f"https://{website_url}"
            try:
                hostname = Url(candidate).hostname
            except Exception:  # noqa: BLE001 - a malformed website tag must not break discovery
                hostname = None

        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lon = element.get("lon") or (element.get("center") or {}).get("lon")
        address_parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
        ]
        address = " ".join(p for p in address_parts if p) or None

        return DiscoveredBusiness(
            name=name,
            category=category,
            website=hostname,
            website_url=website_url,
            phone=tags.get("phone") or tags.get("contact:phone"),
            address=address,
            city=tags.get("addr:city"),
            state=tags.get("addr:state"),
            country=tags.get("addr:country"),
            postal_code=tags.get("addr:postcode"),
            latitude=float(lat) if lat is not None else None,
            longitude=float(lon) if lon is not None else None,
            source_url=(
                f"https://www.openstreetmap.org/{element.get('type')}/{element.get('id')}"
                if element.get("id")
                else None
            ),
        )

    def close(self) -> None:
        self._client.close()
