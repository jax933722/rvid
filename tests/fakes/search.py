"""In-memory reference implementation of :class:`SearchIndexPort`.

Exists so the same contract suite can validate both the SQL adapter and a
pure-Python implementation — the proof that any future backend (OpenSearch) can
drop in behind the port without changing business logic.
"""

from __future__ import annotations

from collections import Counter

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


class InMemorySearchIndex:
    """A dict-backed SearchIndexPort with the same semantics as the SQL adapter."""

    def __init__(self) -> None:
        self._docs: dict[int, SearchDocument] = {}

    def upsert(self, document: SearchDocument) -> None:
        self._docs[document.company_id] = document

    def search(self, query: CompiledQuery) -> SearchResult:
        matched = [d for d in self._docs.values() if self._matches(d, query)]
        matched.sort(key=lambda d: (-(d.seo_score or -1.0), d.display_name))
        if query.sort.field == "name":
            matched.sort(key=lambda d: d.display_name, reverse=query.sort.descending)
        elif query.sort.field == "recency":
            matched.sort(key=lambda d: d.indexed_at, reverse=query.sort.descending)

        total = len(matched)
        start = (query.page - 1) * query.page_size
        page = matched[start : start + query.page_size]
        return SearchResult(
            items=[self._to_item(d) for d in page],
            facets=self._facets(matched, query.facets),
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    # --- semantics ---------------------------------------------------------
    def _matches(self, doc: SearchDocument, query: CompiledQuery) -> bool:
        if query.text:
            needle = query.text.lower()
            if needle not in doc.text_blob.lower() and needle not in doc.display_name.lower():
                return False
        return all(self._predicate(doc, p) for p in query.predicates)

    @staticmethod
    def _predicate(doc: SearchDocument, p: Predicate) -> bool:
        if p.kind is FieldKind.LIST:
            source = doc.roles if p.field == "role" else doc.technologies
            owned = {t.lower() for t in source}
            return any(v.lower() in owned for v in p.values)

        value = getattr(doc, p.field)
        if p.kind is FieldKind.NUMBER:
            if value is None:
                return False
            if p.op is FilterOp.BETWEEN:
                return float(p.values[0]) <= float(value) <= float(p.values[1])
            target = float(p.values[0])
            if p.op is FilterOp.GTE:
                return float(value) >= target
            if p.op is FilterOp.LTE:
                return float(value) <= target
            return float(value) == target
        if p.kind is FieldKind.BOOL:
            if p.op is FilterOp.IS_TRUE:
                return bool(value) is True
            return bool(value) is (p.values[0].lower() in ("true", "1", "yes"))
        # TEXT
        if p.op is FilterOp.IN:
            return value in p.values
        return value == p.values[0]

    @staticmethod
    def _to_item(doc: SearchDocument) -> SearchResultItem:
        return SearchResultItem(
            company_id=doc.company_id,
            display_name=doc.display_name,
            primary_domain=doc.primary_domain,
            industry=doc.industry,
            country=doc.country,
            state=doc.state,
            city=doc.city,
            size_bucket=doc.size_bucket,
            founded_year=doc.founded_year,
            employee_count=doc.employee_count,
            seo_score=doc.seo_score,
            seo_grade=doc.seo_grade,
            technologies=list(doc.technologies),
        )

    @staticmethod
    def _facets(docs: list[SearchDocument], fields: tuple[str, ...]) -> dict[str, list[FacetValue]]:
        result: dict[str, list[FacetValue]] = {}
        for field in fields:
            counter: Counter[str] = Counter()
            for doc in docs:
                if field == "technology":
                    counter.update(doc.technologies)
                elif field == "role":
                    counter.update(doc.roles)
                else:
                    value = getattr(doc, field)
                    if value is not None:
                        counter.update([str(value)])
            result[field] = [FacetValue(value=v, count=c) for v, c in counter.most_common()]
        return result
