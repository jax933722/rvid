"""Integration test: ExtractPeople end to end against SQLite."""

from __future__ import annotations

from config.containers import Container

from bise.application.use_cases.enrichment.extract_people import ExtractPeople
from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.domain.entities.person import EmailStatus, RoleCategory
from bise.domain.entities.website_domain import WebsiteDomain
from bise.infrastructure.analyzers.team_extractor import RuleBasedTeamExtractor

TEAM_HTML = """
<html><body>
<div class="team-member"><h3>Jane Doe</h3><p class="role">Founder &amp; CEO</p>
  <a href="mailto:jane.doe@acme.com">email</a></div>
<div class="team-member"><h3>John Smith</h3><p class="role">Chief Technology Officer</p></div>
</body></html>
"""


def _seed(container: Container) -> int:
    company = Company(display_name="Acme")
    company.add_domain(WebsiteDomain(hostname="acme.com"))
    with container.unit_of_work() as uow:
        saved = uow.companies.add(company)
        company_id = saved.id
        domain_id = saved.domains[0].id
        assert company_id is not None and domain_id is not None
        job = uow.crawl_jobs.add(CrawlJob(domain_id=domain_id, hostname="acme.com"))
        uow.crawled_pages.add(
            CrawledPage(
                domain_id=domain_id,
                crawl_job_id=job.id,
                url="https://acme.com/about",
                page_type=PageType.ABOUT,
                http_status=200,
                content_hash="h",
                html=TEAM_HTML,
            )
        )
        uow.commit()
        return company_id


def test_extract_classifies_roles_and_fills_emails(container: Container) -> None:
    company_id = _seed(container)
    people = ExtractPeople(container.unit_of_work(), RuleBasedTeamExtractor()).execute(company_id)

    by_name = {p.name: p for p in people}
    assert by_name["Jane Doe"].role_category == RoleCategory.FOUNDER.value
    assert by_name["Jane Doe"].email == "jane.doe@acme.com"
    assert by_name["Jane Doe"].email_status == EmailStatus.PUBLISHED.value

    # John's email is inferred from Jane's observed "{first}.{last}" pattern.
    assert by_name["John Smith"].role_category == RoleCategory.CTO.value
    assert by_name["John Smith"].email == "john.smith@acme.com"
    assert by_name["John Smith"].email_status == EmailStatus.GUESSED.value


def test_extract_is_idempotent(container: Container) -> None:
    company_id = _seed(container)
    extract = ExtractPeople(container.unit_of_work(), RuleBasedTeamExtractor())
    extract.execute(company_id)
    extract.execute(company_id)
    with container.unit_of_work() as uow:
        assert len(uow.people.list_for_company(company_id)) == 2  # replaced, not duplicated
