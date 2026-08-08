"""Integration tests: lead-engine use cases against SQLite (fake discovery)."""

from __future__ import annotations

from config.containers import Container

from bise.application.dto.lead_dto import CreateLeadCampaignCommand
from bise.application.ports.discovery import DiscoveredBusiness
from bise.application.use_cases.leads.list_leads import ListLeads
from bise.application.use_cases.leads.manage_campaigns import (
    CreateLeadCampaign,
    DeleteLeadCampaign,
    ListLeadCampaigns,
)
from bise.application.use_cases.leads.run_lead_campaign import RunLeadCampaign
from tests.fakes.discovery import KeyedFakeDiscoverySource


def _biz(name: str, website: str, category: str, city: str) -> DiscoveredBusiness:
    return DiscoveredBusiness(
        name=name,
        category=category,
        website=website,
        website_url=f"https://{website}",
        city=city,
    )


def _source() -> KeyedFakeDiscoverySource:
    # A 2x1 grid: "dentist"/"plumber" x "Sydney". Each cell has its own businesses.
    return KeyedFakeDiscoverySource(
        {
            ("dentist", "Sydney"): [
                _biz("Acme Dental", "acmedental.com", "dentist", "Sydney"),
                _biz("Bright Dental", "brightdental.com", "dentist", "Sydney"),
                _biz("No Website Dental", "", "dentist", "Sydney"),
            ],
            ("plumber", "Sydney"): [
                _biz("Fast Pipes", "fastpipes.com", "plumber", "Sydney"),
            ],
        }
    )


def _create(container: Container, **overrides: object) -> int:
    command = CreateLeadCampaignCommand(
        name=overrides.get("name", "AU trades"),  # type: ignore[arg-type]
        categories=overrides.get("categories", ("dentist", "plumber")),  # type: ignore[arg-type]
        locations=overrides.get("locations", ("Sydney",)),  # type: ignore[arg-type]
        auto_enrich=overrides.get("auto_enrich", True),  # type: ignore[arg-type]
    )
    dto = CreateLeadCampaign(container.unit_of_work()).execute(command)
    assert dto.id is not None
    return dto.id


def test_create_campaign_cleans_and_reports_grid(container: Container) -> None:
    dto = CreateLeadCampaign(container.unit_of_work()).execute(
        CreateLeadCampaignCommand(
            name="  AU trades ",
            categories=("dentist", " dentist ", "plumber"),  # dup + whitespace
            locations=("Sydney",),
        )
    )
    assert dto.name == "AU trades"
    assert dto.categories == ("dentist", "plumber")
    assert dto.grid_size == 2
    assert dto.lead_count == 0
    assert dto.next_target == ("dentist", "Sydney")


def test_run_records_only_websites_as_leads_and_enqueues(container: Container) -> None:
    campaign_id = _create(container)
    source = _source()
    result = RunLeadCampaign(container.unit_of_work(), source).execute(campaign_id)

    # First cell = ("dentist", "Sydney"): 3 found, 2 have websites -> 2 leads.
    assert result.category == "dentist"
    assert result.found == 3
    assert result.new_leads == 2
    assert result.enqueued_enrichment == 2

    with container.unit_of_work() as uow:
        assert uow.leads.count_for_campaign(campaign_id) == 2
        # Auto-enrich queued a job for each new company.
        assert uow.enrichment_jobs.next_pending() is not None


def test_rotation_sweeps_next_cell_and_dedups(container: Container) -> None:
    campaign_id = _create(container)
    source = _source()
    run = RunLeadCampaign(container.unit_of_work(), source)

    first = run.execute(campaign_id)  # dentist/Sydney -> 2 new
    second = run.execute(campaign_id)  # cursor advanced -> plumber/Sydney -> 1 new
    third = run.execute(campaign_id)  # wrapped back to dentist/Sydney -> 0 new (dedup)

    assert first.category == "dentist"
    assert second.category == "plumber"
    assert second.new_leads == 1
    assert third.category == "dentist"
    assert third.new_leads == 0  # already-seen companies never re-surface
    assert source.calls == [
        ("dentist", "Sydney"),
        ("plumber", "Sydney"),
        ("dentist", "Sydney"),
    ]

    with container.unit_of_work() as uow:
        assert uow.leads.count_for_campaign(campaign_id) == 3


def test_run_without_auto_enrich_skips_queue(container: Container) -> None:
    campaign_id = _create(container, auto_enrich=False)
    result = RunLeadCampaign(container.unit_of_work(), _source()).execute(campaign_id)

    assert result.new_leads == 2
    assert result.enqueued_enrichment == 0
    with container.unit_of_work() as uow:
        assert uow.enrichment_jobs.next_pending() is None


def test_list_campaigns_and_leads_reflect_runs(container: Container) -> None:
    campaign_id = _create(container)
    RunLeadCampaign(container.unit_of_work(), _source()).execute(campaign_id)

    campaigns = ListLeadCampaigns(container.unit_of_work()).execute()
    assert len(campaigns) == 1
    assert campaigns[0].lead_count == 2
    assert campaigns[0].last_run_at is not None

    leads = ListLeads(container.unit_of_work()).execute()
    assert {lead.company.display_name for lead in leads} == {"Acme Dental", "Bright Dental"}
    assert all(lead.status == "new" for lead in leads)


def test_delete_campaign_removes_its_leads(container: Container) -> None:
    campaign_id = _create(container)
    RunLeadCampaign(container.unit_of_work(), _source()).execute(campaign_id)

    assert DeleteLeadCampaign(container.unit_of_work()).execute(campaign_id) is True
    assert ListLeadCampaigns(container.unit_of_work()).execute() == []
    with container.unit_of_work() as uow:
        assert uow.leads.count_for_campaign(campaign_id) == 0
