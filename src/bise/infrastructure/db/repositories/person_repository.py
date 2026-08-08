"""SQLAlchemy implementation of :class:`PersonRepository`."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from bise.domain.entities.person import EmailStatus, Person, RoleCategory
from bise.infrastructure.db.models.person import PersonModel

# Sort order for display: most senior roles first.
_ROLE_RANK = {
    RoleCategory.FOUNDER: 0,
    RoleCategory.CEO: 1,
    RoleCategory.CTO: 2,
    RoleCategory.CFO: 3,
    RoleCategory.COO: 4,
    RoleCategory.CMO: 5,
    RoleCategory.VP: 6,
    RoleCategory.DIRECTOR: 7,
    RoleCategory.HEAD: 8,
    RoleCategory.MANAGER: 9,
    RoleCategory.OTHER: 10,
}


def _to_entity(model: PersonModel) -> Person:
    return Person(
        id=model.id,
        company_id=model.company_id,
        name=model.name,
        title=model.title,
        role_category=RoleCategory(model.role_category),
        email=model.email,
        email_status=EmailStatus(model.email_status),
        source_url=model.source_url,
        created_at=model.created_at,
    )


class SqlAlchemyPersonRepository:
    """People persistence backed by a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def replace_for_company(self, company_id: int, people: list[Person]) -> None:
        self._session.execute(delete(PersonModel).where(PersonModel.company_id == company_id))
        for person in people:
            self._session.add(
                PersonModel(
                    company_id=company_id,
                    name=person.name,
                    title=person.title,
                    role_category=person.role_category.value,
                    email=person.email,
                    email_status=person.email_status.value,
                    source_url=person.source_url,
                )
            )
        self._session.flush()

    def list_for_company(self, company_id: int) -> Sequence[Person]:
        stmt = (
            select(PersonModel)
            .where(PersonModel.company_id == company_id)
            .order_by(PersonModel.name.asc())
        )
        people = [_to_entity(m) for m in self._session.scalars(stmt).all()]
        people.sort(key=lambda p: (_ROLE_RANK[p.role_category], p.name.lower()))
        return people
