"""SQLAlchemy implementation of :class:`CompanyRepository`.

Maps between ORM models (``CompanyModel``/``DomainModel``) and domain entities
(``Company``/``WebsiteDomain``) so the domain stays persistence-agnostic.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bise.domain.entities.company import Company, CompanyStatus
from bise.domain.entities.website_domain import CrawlStatus, WebsiteDomain
from bise.infrastructure.db.models.company import CompanyModel, DomainModel
from bise.shared.pagination import Page, PageRequest


def _to_entity(model: CompanyModel) -> Company:
    return Company(
        id=model.id,
        display_name=model.display_name,
        legal_name=model.legal_name,
        status=CompanyStatus(model.status),
        industry=model.industry,
        size_bucket=model.size_bucket,
        country=model.country,
        state=model.state,
        city=model.city,
        founded_year=model.founded_year,
        employee_count=model.employee_count,
        contact_email=model.contact_email,
        contact_phone=model.contact_phone,
        created_at=model.created_at,
        updated_at=model.updated_at,
        domains=[
            WebsiteDomain(
                id=d.id,
                hostname=d.hostname,
                is_primary=d.is_primary,
                crawl_status=CrawlStatus(d.crawl_status),
            )
            for d in model.domains
        ],
    )


def _to_model(entity: Company) -> CompanyModel:
    return CompanyModel(
        display_name=entity.display_name,
        legal_name=entity.legal_name,
        status=entity.status.value,
        industry=entity.industry,
        size_bucket=entity.size_bucket,
        country=entity.country,
        state=entity.state,
        city=entity.city,
        founded_year=entity.founded_year,
        employee_count=entity.employee_count,
        contact_email=entity.contact_email,
        contact_phone=entity.contact_phone,
        domains=[
            DomainModel(
                hostname=d.hostname,
                is_primary=d.is_primary,
                crawl_status=d.crawl_status.value,
            )
            for d in entity.domains
        ],
    )


class SqlAlchemyCompanyRepository:
    """Company persistence backed by a SQLAlchemy :class:`Session`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, company: Company) -> Company:
        model = _to_model(company)
        self._session.add(model)
        self._session.flush()  # assign primary keys without committing
        return _to_entity(model)

    def get(self, company_id: int) -> Company | None:
        model = self._session.get(CompanyModel, company_id)
        return _to_entity(model) if model is not None else None

    def find_by_hostname(self, hostname: str) -> Company | None:
        stmt = (
            select(CompanyModel).join(DomainModel).where(DomainModel.hostname == hostname.lower())
        )
        model = self._session.scalars(stmt).first()
        return _to_entity(model) if model is not None else None

    def list(self, page: PageRequest) -> Page[Company]:
        total = self._session.scalar(select(func.count()).select_from(CompanyModel)) or 0
        stmt = (
            select(CompanyModel)
            .order_by(CompanyModel.created_at.desc(), CompanyModel.id.desc())
            .offset(page.offset)
            .limit(page.limit)
        )
        models = self._session.scalars(stmt).all()
        return Page(
            items=[_to_entity(m) for m in models],
            total=total,
            page=page.page,
            page_size=page.page_size,
        )

    def mark_domain_crawl_status(self, domain_id: int, status: CrawlStatus) -> None:
        model = self._session.get(DomainModel, domain_id)
        if model is None:
            raise KeyError(f"Domain not found: {domain_id}")
        model.crawl_status = status.value
        self._session.flush()
