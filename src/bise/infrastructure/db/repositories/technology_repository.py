"""SQLAlchemy implementations of the technology repositories."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from bise.domain.entities.technology import CompanyTechnology, Technology
from bise.domain.value_objects.confidence import Confidence
from bise.infrastructure.db.models.technology import (
    CompanyTechnologyModel,
    TechnologyCategoryModel,
    TechnologyModel,
)
from bise.shared.pagination import Page, PageRequest


def _tech_to_entity(model: TechnologyModel) -> Technology:
    return Technology(
        id=model.id,
        name=model.name,
        category=model.category.name,
        vendor=model.vendor,
    )


class SqlAlchemyTechnologyRepository:
    """Canonical technology reference data, keyed by unique name."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _get_or_create_category(self, name: str) -> TechnologyCategoryModel:
        existing = self._session.scalars(
            select(TechnologyCategoryModel).where(TechnologyCategoryModel.name == name)
        ).first()
        if existing is not None:
            return existing
        category = TechnologyCategoryModel(name=name)
        self._session.add(category)
        self._session.flush()
        return category

    def get_or_create(self, name: str, category: str, vendor: str | None = None) -> Technology:
        existing = self._session.scalars(
            select(TechnologyModel).where(TechnologyModel.name == name)
        ).first()
        if existing is not None:
            return _tech_to_entity(existing)

        category_model = self._get_or_create_category(category)
        model = TechnologyModel(name=name, vendor=vendor, category_id=category_model.id)
        self._session.add(model)
        self._session.flush()
        return _tech_to_entity(model)

    def list(self, page: PageRequest) -> Page[Technology]:
        total = self._session.scalar(select(func.count()).select_from(TechnologyModel)) or 0
        stmt = (
            select(TechnologyModel)
            .order_by(TechnologyModel.name)
            .offset(page.offset)
            .limit(page.limit)
        )
        models = self._session.scalars(stmt).all()
        return Page(
            items=[_tech_to_entity(m) for m in models],
            total=total,
            page=page.page,
            page_size=page.page_size,
        )


class SqlAlchemyCompanyTechnologyRepository:
    """Company↔technology detections with evidence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def replace_for_company(self, company_id: int, detections: list[CompanyTechnology]) -> None:
        self._session.execute(
            delete(CompanyTechnologyModel).where(CompanyTechnologyModel.company_id == company_id)
        )
        for det in detections:
            self._session.add(
                CompanyTechnologyModel(
                    company_id=company_id,
                    technology_id=det.technology_id,
                    confidence=float(det.confidence),
                    evidence=det.evidence,
                    version=det.version,
                    detected_at=det.detected_at,
                )
            )
        self._session.flush()

    def list_for_company(self, company_id: int) -> list[CompanyTechnology]:
        stmt = (
            select(CompanyTechnologyModel)
            .where(CompanyTechnologyModel.company_id == company_id)
            .order_by(CompanyTechnologyModel.id)
        )
        return [
            CompanyTechnology(
                id=m.id,
                company_id=m.company_id,
                technology_id=m.technology_id,
                confidence=Confidence(m.confidence),
                evidence=m.evidence or "",
                version=m.version,
                detected_at=m.detected_at,
                technology=_tech_to_entity(m.technology),
            )
            for m in self._session.scalars(stmt).all()
        ]
