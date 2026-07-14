"""SQLAlchemy implementations of the workspace-scoped personal-data repositories.

Covers saved searches, company lists (with membership), and company tags. Every
read and write is scoped to a workspace so one tenant never sees another's work.
Maps between ORM models and domain entities so the domain stays persistence-agnostic.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bise.domain.entities.company import Company
from bise.domain.entities.company_list import CompanyList
from bise.domain.entities.company_tag import CompanyTag
from bise.domain.entities.saved_search import SavedSearch
from bise.infrastructure.db.models.company import CompanyModel
from bise.infrastructure.db.models.workspace import (
    CompanyListItemModel,
    CompanyListModel,
    CompanyTagModel,
    SavedSearchModel,
)
from bise.infrastructure.db.repositories.company_repository import _to_entity as _company_to_entity


class SqlAlchemySavedSearchRepository:
    """Saved-search persistence backed by a SQLAlchemy :class:`Session`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, search: SavedSearch) -> SavedSearch:
        assert search.workspace_id is not None, "saved search requires a workspace"
        model = SavedSearchModel(
            workspace_id=search.workspace_id,
            name=search.name,
            query_json=search.query_json,
        )
        self._session.add(model)
        self._session.flush()
        return self._to_entity(model)

    def get(self, workspace_id: int, search_id: int) -> SavedSearch | None:
        model = self._session.scalars(
            select(SavedSearchModel).where(
                SavedSearchModel.id == search_id,
                SavedSearchModel.workspace_id == workspace_id,
            )
        ).first()
        return self._to_entity(model) if model is not None else None

    def list(self, workspace_id: int) -> Sequence[SavedSearch]:
        stmt = (
            select(SavedSearchModel)
            .where(SavedSearchModel.workspace_id == workspace_id)
            .order_by(SavedSearchModel.created_at.desc(), SavedSearchModel.id.desc())
        )
        return [self._to_entity(m) for m in self._session.scalars(stmt).all()]

    def delete(self, workspace_id: int, search_id: int) -> bool:
        model = self._session.scalars(
            select(SavedSearchModel).where(
                SavedSearchModel.id == search_id,
                SavedSearchModel.workspace_id == workspace_id,
            )
        ).first()
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    @staticmethod
    def _to_entity(model: SavedSearchModel) -> SavedSearch:
        return SavedSearch(
            id=model.id,
            workspace_id=model.workspace_id,
            name=model.name,
            query_json=model.query_json,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyCompanyListRepository:
    """Company-list persistence (lists + membership), scoped to a workspace."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, company_list: CompanyList) -> CompanyList:
        assert company_list.workspace_id is not None, "list requires a workspace"
        model = CompanyListModel(
            workspace_id=company_list.workspace_id,
            name=company_list.name,
            description=company_list.description,
        )
        self._session.add(model)
        self._session.flush()
        return self._to_entity(model, member_count=0)

    def get(self, workspace_id: int, list_id: int) -> CompanyList | None:
        model = self._session.scalars(
            select(CompanyListModel).where(
                CompanyListModel.id == list_id,
                CompanyListModel.workspace_id == workspace_id,
            )
        ).first()
        if model is None:
            return None
        return self._to_entity(model, member_count=self._count(list_id))

    def list(self, workspace_id: int) -> Sequence[CompanyList]:
        stmt = (
            select(CompanyListModel)
            .where(CompanyListModel.workspace_id == workspace_id)
            .order_by(CompanyListModel.created_at.desc(), CompanyListModel.id.desc())
        )
        return [
            self._to_entity(m, member_count=self._count(m.id))
            for m in self._session.scalars(stmt).all()
        ]

    def delete(self, workspace_id: int, list_id: int) -> bool:
        model = self._session.scalars(
            select(CompanyListModel).where(
                CompanyListModel.id == list_id,
                CompanyListModel.workspace_id == workspace_id,
            )
        ).first()
        if model is None:
            return False
        self._session.delete(model)  # cascade removes memberships
        self._session.flush()
        return True

    def add_company(self, list_id: int, company_id: int) -> bool:
        exists = self._session.scalar(
            select(CompanyListItemModel.id).where(
                CompanyListItemModel.list_id == list_id,
                CompanyListItemModel.company_id == company_id,
            )
        )
        if exists is not None:
            return False
        self._session.add(CompanyListItemModel(list_id=list_id, company_id=company_id))
        self._session.flush()
        return True

    def remove_company(self, list_id: int, company_id: int) -> bool:
        item = self._session.scalar(
            select(CompanyListItemModel).where(
                CompanyListItemModel.list_id == list_id,
                CompanyListItemModel.company_id == company_id,
            )
        )
        if item is None:
            return False
        self._session.delete(item)
        self._session.flush()
        return True

    def list_members(self, list_id: int) -> Sequence[Company]:
        stmt = (
            select(CompanyModel)
            .join(CompanyListItemModel, CompanyListItemModel.company_id == CompanyModel.id)
            .where(CompanyListItemModel.list_id == list_id)
            .order_by(CompanyListItemModel.id.desc())
        )
        return [_company_to_entity(m) for m in self._session.scalars(stmt).all()]

    def _count(self, list_id: int | None) -> int:
        if list_id is None:
            return 0
        return (
            self._session.scalar(
                select(func.count())
                .select_from(CompanyListItemModel)
                .where(CompanyListItemModel.list_id == list_id)
            )
            or 0
        )

    @staticmethod
    def _to_entity(model: CompanyListModel, member_count: int) -> CompanyList:
        return CompanyList(
            id=model.id,
            workspace_id=model.workspace_id,
            name=model.name,
            description=model.description,
            member_count=member_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyCompanyTagRepository:
    """Company-tag persistence (normalized labels), scoped to a workspace."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, tag: CompanyTag) -> CompanyTag:
        assert tag.workspace_id is not None, "tag requires a workspace"
        existing = self._session.scalar(
            select(CompanyTagModel).where(
                CompanyTagModel.workspace_id == tag.workspace_id,
                CompanyTagModel.company_id == tag.company_id,
                CompanyTagModel.label == tag.label,
            )
        )
        if existing is not None:
            return self._to_entity(existing)
        model = CompanyTagModel(
            workspace_id=tag.workspace_id, company_id=tag.company_id, label=tag.label
        )
        self._session.add(model)
        self._session.flush()
        return self._to_entity(model)

    def remove(self, workspace_id: int, company_id: int, label: str) -> bool:
        model = self._session.scalar(
            select(CompanyTagModel).where(
                CompanyTagModel.workspace_id == workspace_id,
                CompanyTagModel.company_id == company_id,
                CompanyTagModel.label == label.strip().lower(),
            )
        )
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def list_for_company(self, workspace_id: int, company_id: int) -> Sequence[CompanyTag]:
        stmt = (
            select(CompanyTagModel)
            .where(
                CompanyTagModel.workspace_id == workspace_id,
                CompanyTagModel.company_id == company_id,
            )
            .order_by(CompanyTagModel.label.asc())
        )
        return [self._to_entity(m) for m in self._session.scalars(stmt).all()]

    @staticmethod
    def _to_entity(model: CompanyTagModel) -> CompanyTag:
        return CompanyTag(
            id=model.id,
            workspace_id=model.workspace_id,
            company_id=model.company_id,
            label=model.label,
            created_at=model.created_at,
        )
