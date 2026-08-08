"""Integration tests for the lead-engine worker (run_due_campaigns)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from config.containers import Container

from bise.application.dto.lead_dto import CreateLeadCampaignCommand
from bise.application.ports.discovery import DiscoveredBusiness
from bise.application.use_cases.leads.manage_campaigns import CreateLeadCampaign
from bise.presentation.workers.lead_engine import run_due_campaigns
from tests.fakes.discovery import KeyedFakeDiscoverySource


def _biz(name: str, website: str, category: str) -> DiscoveredBusiness:
    return DiscoveredBusiness(
        name=name, category=category, website=website, website_url=f"https://{website}"
    )


def _wire(container: Container) -> None:
    container._discovery_source = KeyedFakeDiscoverySource(  # noqa: SLF001 - test wiring
        {
            ("dentist", "Sydney"): [_biz("Acme Dental", "acme.com", "dentist")],
            ("plumber", "Melbourne"): [_biz("Fast Pipes", "fastpipes.com", "plumber")],
        }
    )


def _create(container: Container, name: str, category: str, location: str, interval: int) -> int:
    dto = CreateLeadCampaign(container.unit_of_work()).execute(
        CreateLeadCampaignCommand(
            name=name,
            categories=(category,),
            locations=(location,),
            interval_minutes=interval,
            auto_enrich=False,
        )
    )
    assert dto.id is not None
    return dto.id


def test_runs_all_due_campaigns(container: Container) -> None:
    _wire(container)
    _create(container, "Dentists", "dentist", "Sydney", interval=60)
    _create(container, "Plumbers", "plumber", "Melbourne", interval=60)

    # Both are never-run, so both are due.
    new_leads = run_due_campaigns(container)
    assert new_leads == 2


def test_skips_campaigns_not_yet_due(container: Container) -> None:
    _wire(container)
    campaign_id = _create(container, "Dentists", "dentist", "Sydney", interval=60)

    # First tick runs it.
    assert run_due_campaigns(container) == 1
    # A second tick moments later finds nothing due (interval not elapsed).
    assert run_due_campaigns(container, now=datetime.now(UTC)) == 0
    # Far enough in the future it becomes due again — but its only company is a
    # dedup hit, so no new leads surface.
    later = datetime.now(UTC) + timedelta(minutes=61)
    assert run_due_campaigns(container, now=later) == 0

    with container.unit_of_work() as uow:
        assert uow.leads.count_for_campaign(campaign_id) == 1


def test_one_failing_campaign_does_not_stop_others(container: Container) -> None:
    _wire(container)
    good = _create(container, "Dentists", "dentist", "Sydney", interval=60)
    # A campaign whose discovery source raises when queried.
    boom = _create(container, "Boom", "explosives", "Nowhere", interval=60)

    class Boom(KeyedFakeDiscoverySource):
        def discover(self, criteria):  # type: ignore[no-untyped-def]
            if criteria.category == "explosives":
                raise RuntimeError("discovery blew up")
            return super().discover(criteria)

    container._discovery_source = Boom(  # noqa: SLF001 - test wiring
        {("dentist", "Sydney"): [_biz("Acme Dental", "acme.com", "dentist")]}
    )

    # The good campaign still produces its lead despite the other failing.
    new_leads = run_due_campaigns(container)
    assert new_leads == 1
    with container.unit_of_work() as uow:
        assert uow.leads.count_for_campaign(good) == 1
        assert uow.leads.count_for_campaign(boom) == 0
