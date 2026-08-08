"""Use case: extract a company's people (and their emails) from its site.

Reads the pages captured by the crawler (no re-fetch), runs the extractor, then:
  * classifies each person's title into a RoleCategory,
  * attaches emails published on the site (matched to the person by name),
  * learns the company's email pattern from any published personal email and
    fills gaps for colleagues (labelled ``GUESSED``, i.e. unverified).
Idempotent — replaces the company's people on each run.
"""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.person_dto import PersonDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import person_to_dto
from bise.application.ports.person_extractor import (
    ExtractedPerson,
    PageContent,
    PersonExtractorPort,
)
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.crawled_page import PageType
from bise.domain.entities.person import EmailStatus, Person
from bise.domain.services.people import (
    apply_email_pattern,
    classify_role,
    infer_email_pattern,
)

logger = get_logger(__name__)

# Pages most likely to list people; keeps parsing focused and cheap.
_PEOPLE_PAGES = {PageType.ABOUT, PageType.CONTACT, PageType.HOME, PageType.CAREERS}


class ExtractPeople:
    """Detect and persist the people published on a company's website."""

    def __init__(self, uow: UnitOfWork, extractor: PersonExtractorPort) -> None:
        self._uow = uow
        self._extractor = extractor

    def execute(self, company_id: int) -> list[PersonDTO]:
        with self._uow as uow:
            company = uow.companies.get(company_id)
            if company is None:
                raise NotFoundError(f"Company not found: {company_id}")
            domain = company.primary_domain.hostname if company.primary_domain else None

            pages: list[PageContent] = []
            for website in company.domains:
                if website.id is None:
                    continue
                for page in uow.crawled_pages.list_for_domain(website.id):
                    if page.page_type in _PEOPLE_PAGES:
                        pages.append(PageContent(url=page.url, html=page.html or ""))

            extraction = self._extractor.extract(pages)
            people = self._resolve(extraction.people, extraction.emails, company_id, domain)
            uow.people.replace_for_company(company_id, people)
            uow.commit()

        logger.info("people.extracted", company_id=company_id, count=len(people))
        return [person_to_dto(p) for p in people]

    @staticmethod
    def _resolve(
        raw_people: list[ExtractedPerson],
        emails: list[str],
        company_id: int,
        domain: str | None,
    ) -> list[Person]:
        on_domain = [e for e in emails if domain and e.endswith(f"@{domain}")]

        people: list[Person] = []
        for raw in raw_people:
            email = raw.email
            status = EmailStatus.PUBLISHED if email else EmailStatus.NONE
            # Match an on-domain published email to this person by name.
            if email is None:
                match = next(
                    (e for e in on_domain if infer_email_pattern(raw.name, e) is not None), None
                )
                if match is not None:
                    email, status = match, EmailStatus.PUBLISHED
            people.append(
                Person(
                    company_id=company_id,
                    name=raw.name,
                    title=raw.title,
                    role_category=classify_role(raw.title),
                    email=email,
                    email_status=status,
                    source_url=raw.source_url,
                )
            )

        # Learn the company's email pattern from any matched personal email...
        pattern = _learn_pattern(people, domain)
        # ...and fill gaps for colleagues (clearly labelled as guessed).
        if pattern is not None and domain is not None:
            for person in people:
                if person.email is None:
                    guess = apply_email_pattern(person.name, domain, pattern)
                    if guess is not None:
                        person.email = guess
                        person.email_status = EmailStatus.GUESSED
        return people


def _learn_pattern(people: list[Person], domain: str | None) -> str | None:
    if domain is None:
        return None
    for person in people:
        if person.email and person.email.endswith(f"@{domain}"):
            pattern = infer_email_pattern(person.name, person.email)
            if pattern is not None:
                return pattern
    return None
