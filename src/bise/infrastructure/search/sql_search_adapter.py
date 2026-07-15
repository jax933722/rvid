"""Portable SQL search adapter — the FTS-now implementation of SearchIndexPort.

Renders a validated :class:`CompiledQuery` into SQLAlchemy against the
``search_documents`` projection. Uses only portable constructs (LIKE, column
comparisons) so the same adapter serves SQLite (dev) and PostgreSQL (prod). A
true PostgreSQL ``tsvector`` adapter or an OpenSearch adapter can replace it
later behind the same port, with no change to business logic.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any

from sqlalchemy import ColumnElement, Select, and_, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute, Session, sessionmaker

from bise.application.dto.search_dto import (
    FacetValue,
    FilterOp,
    SearchResult,
    SearchResultItem,
)
from bise.application.use_cases.search.compile_query import (
    CompiledQuery,
    FieldKind,
    Predicate,
)
from bise.domain.entities.search_document import SearchDocument
from bise.infrastructure.db.models.search import SearchDocumentModel

_M = SearchDocumentModel


def _tech_text(technologies: list[str]) -> str:
    if not technologies:
        return ""
    return "|" + "|".join(t.lower() for t in technologies) + "|"


class SqlSearchAdapter:
    """SearchIndexPort backed by the ``search_documents`` table (SQLite/Postgres)."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # --- indexing ----------------------------------------------------------
    def upsert(self, document: SearchDocument) -> None:
        with self._session_factory() as session:
            model = session.get(SearchDocumentModel, document.company_id)
            if model is None:
                model = SearchDocumentModel(company_id=document.company_id)
                session.add(model)
            self._apply(document, model)
            session.commit()

    @staticmethod
    def _apply(doc: SearchDocument, model: SearchDocumentModel) -> None:
        model.display_name = doc.display_name
        model.primary_domain = doc.primary_domain
        model.industry = doc.industry
        model.country = doc.country
        model.state = doc.state
        model.city = doc.city
        model.size_bucket = doc.size_bucket
        model.founded_year = doc.founded_year
        model.employee_count = doc.employee_count
        model.seo_score = doc.seo_score
        model.seo_grade = doc.seo_grade
        model.technologies = doc.technologies
        model.technologies_text = _tech_text(doc.technologies)
        model.roles = doc.roles
        model.roles_text = _tech_text(doc.roles)
        model.has_ssl = doc.has_ssl
        model.has_contact_page = doc.has_contact_page
        model.has_careers_page = doc.has_careers_page
        model.has_blog = doc.has_blog
        model.has_privacy = doc.has_privacy
        model.has_terms = doc.has_terms
        model.text_blob = doc.text_blob
        model.indexed_at = doc.indexed_at

    # --- querying ----------------------------------------------------------
    def search(self, query: CompiledQuery) -> SearchResult:
        conditions = self._conditions(query)
        with self._session_factory() as session:
            total = (
                session.scalar(
                    select(func.count()).select_from(SearchDocumentModel).where(*conditions)
                )
                or 0
            )

            stmt = self._apply_sort(select(SearchDocumentModel).where(*conditions), query)
            offset = (query.page - 1) * query.page_size
            models = session.scalars(stmt.offset(offset).limit(query.page_size)).all()
            items = [self._to_item(m) for m in models]
            facets = self._facets(session, conditions, query.facets)

        return SearchResult(
            items=items,
            facets=facets,
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    # --- internals ---------------------------------------------------------
    def _conditions(self, query: CompiledQuery) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if query.text:
            needle = f"%{query.text.lower()}%"
            conditions.append(
                or_(
                    func.lower(_M.text_blob).like(needle),
                    func.lower(_M.display_name).like(needle),
                )
            )
        conditions.extend(self._predicate(p) for p in query.predicates)
        return conditions

    # Multi-valued fields map to a pipe-delimited text column for LIKE matching.
    _LIST_COLUMNS = {"technology": _M.technologies_text, "role": _M.roles_text}

    def _predicate(self, p: Predicate) -> ColumnElement[bool]:
        if p.kind is FieldKind.LIST:  # CONTAINS (any-of => OR)
            list_column = self._LIST_COLUMNS[p.field]
            clauses = [list_column.like(f"%|{v.lower()}|%") for v in p.values]
            return or_(*clauses)

        column: InstrumentedAttribute[Any] = getattr(_M, p.field)
        if p.kind is FieldKind.NUMBER:
            if p.op is FilterOp.BETWEEN:
                return column.between(float(p.values[0]), float(p.values[1]))
            value = float(p.values[0])
            if p.op is FilterOp.GTE:
                return column >= value
            if p.op is FilterOp.LTE:
                return column <= value
            return column == value
        if p.kind is FieldKind.BOOL:
            if p.op is FilterOp.IS_TRUE:
                return column.is_(True)
            return column.is_(p.values[0].lower() in ("true", "1", "yes"))
        # TEXT
        if p.op is FilterOp.IN:
            return column.in_(list(p.values))
        return column == p.values[0]

    @staticmethod
    def _apply_sort(stmt: Select[Any], query: CompiledQuery) -> Select[Any]:
        field, desc = query.sort.field, query.sort.descending
        if field == "name":
            return stmt.order_by(_M.display_name.asc() if not desc else _M.display_name.desc())
        if field == "recency":
            return stmt.order_by(_M.indexed_at.desc() if desc else _M.indexed_at.asc())
        # relevance and seo_score both rank by score (relevance falls back to score
        # since the portable adapter has no tsvector ranking), then name for stability.
        score_order = _M.seo_score.desc() if desc else _M.seo_score.asc()
        return stmt.order_by(score_order, _M.display_name.asc())

    @staticmethod
    def _to_item(model: SearchDocumentModel) -> SearchResultItem:
        return SearchResultItem(
            company_id=model.company_id,
            display_name=model.display_name,
            primary_domain=model.primary_domain,
            industry=model.industry,
            country=model.country,
            state=model.state,
            city=model.city,
            size_bucket=model.size_bucket,
            founded_year=model.founded_year,
            employee_count=model.employee_count,
            seo_score=model.seo_score,
            seo_grade=model.seo_grade,
            technologies=list(model.technologies or []),
        )

    def _facets(
        self,
        session: Session,
        conditions: Sequence[ColumnElement[bool]],
        facet_fields: tuple[str, ...],
    ) -> dict[str, list[FacetValue]]:
        facets: dict[str, list[FacetValue]] = {}
        for field in facet_fields:
            if field == "technology":
                facets[field] = self._list_facet(session, conditions, _M.technologies)
            elif field == "role":
                facets[field] = self._list_facet(session, conditions, _M.roles)
            else:
                facets[field] = self._column_facet(session, conditions, field)
        return facets

    @staticmethod
    def _column_facet(
        session: Session, conditions: Sequence[ColumnElement[bool]], field: str
    ) -> list[FacetValue]:
        column: InstrumentedAttribute[Any] = getattr(_M, field)
        rows = session.execute(
            select(column, func.count())
            .where(and_(*conditions, column.is_not(None)))
            .group_by(column)
            .order_by(func.count().desc())
        ).all()
        return [FacetValue(value=str(value), count=count) for value, count in rows]

    @staticmethod
    def _list_facet(
        session: Session,
        conditions: Sequence[ColumnElement[bool]],
        column: InstrumentedAttribute[Any],
    ) -> list[FacetValue]:
        rows = session.scalars(select(column).where(*conditions)).all()
        counter: Counter[str] = Counter()
        for values in rows:
            counter.update(values or [])
        return [FacetValue(value=name, count=count) for name, count in counter.most_common()]
