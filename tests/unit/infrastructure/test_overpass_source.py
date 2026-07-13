"""Unit tests for the OpenStreetMap discovery source (offline via MockTransport)."""

from __future__ import annotations

import json

import httpx

from bise.application.ports.discovery import DiscoveryCriteria
from bise.infrastructure.discovery.overpass_source import OverpassDiscoverySource

_NOMINATIM = [{"boundingbox": ["-33.9", "-33.8", "151.1", "151.3"], "display_name": "Sydney"}]
_OVERPASS = {
    "elements": [
        {
            "type": "node",
            "id": 1,
            "lat": -33.85,
            "lon": 151.2,
            "tags": {
                "name": "Acme Dental",
                "amenity": "dentist",
                "website": "https://acmedental.com",
                "phone": "+61 2 5555 0000",
                "addr:housenumber": "1",
                "addr:street": "George St",
                "addr:city": "Sydney",
            },
        },
        {
            "type": "way",
            "id": 2,
            "center": {"lat": -33.86, "lon": 151.21},
            "tags": {"name": "No-Website Dental", "amenity": "dentist"},
        },
    ]
}


def _handler(request: httpx.Request) -> httpx.Response:
    if "nominatim" in request.url.host:
        return httpx.Response(200, text=json.dumps(_NOMINATIM))
    return httpx.Response(200, text=json.dumps(_OVERPASS))


def _source(handler: httpx.MockTransport) -> OverpassDiscoverySource:
    return OverpassDiscoverySource(client=httpx.Client(transport=handler))


def test_maps_osm_tags_to_businesses() -> None:
    source = _source(httpx.MockTransport(_handler))
    results = source.discover(DiscoveryCriteria(category="dentist", location="Sydney"))
    assert len(results) == 2

    acme = results[0]
    assert acme.name == "Acme Dental"
    assert acme.website == "acmedental.com"
    assert acme.phone == "+61 2 5555 0000"
    assert acme.address == "1 George St"
    assert acme.city == "Sydney"
    assert acme.source_url == "https://www.openstreetmap.org/node/1"

    assert results[1].website is None  # no website tag


def test_returns_empty_when_location_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "nominatim" in request.url.host:
            return httpx.Response(200, text="[]")
        return httpx.Response(200, text=json.dumps(_OVERPASS))

    source = _source(httpx.MockTransport(handler))
    assert source.discover(DiscoveryCriteria(category="dentist", location="Nowhere")) == []


def test_unknown_category_uses_name_fallback() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "nominatim" in request.url.host:
            return httpx.Response(200, text=json.dumps(_NOMINATIM))
        captured["query"] = request.content.decode()
        return httpx.Response(200, text=json.dumps({"elements": []}))

    source = _source(httpx.MockTransport(handler))
    source.discover(DiscoveryCriteria(category="artisan cheese shop", location="Sydney"))
    assert "name~" in captured["query"]  # fell back to a name search
