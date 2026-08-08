"""End-to-end tests for the lead engine API (campaigns + inbox, no network)."""

from __future__ import annotations

from config.containers import Container
from fastapi.testclient import TestClient

from bise.application.ports.discovery import DiscoveredBusiness
from tests.fakes.discovery import KeyedFakeDiscoverySource


def _wire_source(container: Container) -> None:
    container._discovery_source = KeyedFakeDiscoverySource(  # noqa: SLF001 - test wiring
        {
            ("dentist", "Sydney"): [
                DiscoveredBusiness(
                    name="Acme Dental",
                    category="dentist",
                    website="acme.com",
                    website_url="https://acme.com",
                    city="Sydney",
                ),
            ],
            ("plumber", "Sydney"): [
                DiscoveredBusiness(
                    name="Fast Pipes",
                    category="plumber",
                    website="fastpipes.com",
                    website_url="https://fastpipes.com",
                    city="Sydney",
                ),
            ],
        }
    )


def _create(client: TestClient) -> int:
    resp = client.post(
        "/api/v1/lead-campaigns",
        json={
            "name": "AU trades",
            "categories": ["dentist", "plumber"],
            "locations": ["Sydney"],
            "auto_enrich": False,
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["grid_size"] == 2
    assert body["next_category"] == "dentist"
    return int(body["id"])


def test_create_run_and_inbox(client: TestClient, container: Container) -> None:
    _wire_source(container)
    campaign_id = _create(client)

    # First run sweeps dentist/Sydney.
    run1 = client.post(f"/api/v1/lead-campaigns/{campaign_id}/run").json()
    assert run1["category"] == "dentist"
    assert run1["new_leads"] == 1

    # Second run advances the cursor to plumber/Sydney.
    run2 = client.post(f"/api/v1/lead-campaigns/{campaign_id}/run").json()
    assert run2["category"] == "plumber"
    assert run2["new_leads"] == 1

    # The inbox shows both leads, freshest first.
    leads = client.get("/api/v1/leads").json()
    assert [lead["company"]["display_name"] for lead in leads] == ["Fast Pipes", "Acme Dental"]

    # The campaign list reflects the accumulated lead count.
    campaigns = client.get("/api/v1/lead-campaigns").json()
    assert campaigns[0]["lead_count"] == 2


def test_run_due_endpoint(client: TestClient, container: Container) -> None:
    _wire_source(container)
    _create(client)  # never-run campaign is due immediately

    result = client.post("/api/v1/lead-campaigns/run-due").json()
    assert result["new_leads"] == 1  # one grid cell per tick
    assert len(client.get("/api/v1/leads").json()) == 1


def test_run_missing_campaign_is_404(client: TestClient) -> None:
    assert client.post("/api/v1/lead-campaigns/999/run").status_code == 404


def test_delete_campaign(client: TestClient, container: Container) -> None:
    _wire_source(container)
    campaign_id = _create(client)
    client.post(f"/api/v1/lead-campaigns/{campaign_id}/run")

    assert client.delete(f"/api/v1/lead-campaigns/{campaign_id}").status_code == 204
    assert client.get("/api/v1/lead-campaigns").json() == []
    assert client.get("/api/v1/leads").json() == []
    assert client.delete(f"/api/v1/lead-campaigns/{campaign_id}").status_code == 404
