"""Search query and result DTOs — the engine-agnostic contract.

The use case speaks these types; it never builds SQL or an OpenSearch DSL. This
is what lets the search backend (SQL FTS now, OpenSearch later) be swapped
without touching business logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class FilterOp(StrEnum):
    """Supported filter operators."""

    EQ = "eq"
    IN = "in"
    GTE = "gte"
    LTE = "lte"
    CONTAINS = "contains"  # list membership (any-of)
    IS_TRUE = "is_true"


@dataclass(frozen=True, slots=True)
class Filter:
    """A single structured constraint on a whitelisted field."""

    field: str
    op: FilterOp
    values: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SortSpec:
    """Result ordering. ``field`` is one of: relevance, seo_score, name, recency."""

    field: str = "relevance"
    descending: bool = True


@dataclass(frozen=True, slots=True)
class SearchQuery:
    """A full search request: free text + filters + facets + sort + paging."""

    text: str | None = None
    filters: tuple[Filter, ...] = ()
    facets: tuple[str, ...] = ()
    sort: SortSpec = field(default_factory=SortSpec)
    page: int = 1
    page_size: int = 25


@dataclass(frozen=True, slots=True)
class SearchResultItem:
    """One company in a search result page."""

    company_id: int
    display_name: str
    primary_domain: str | None
    industry: str | None
    country: str | None
    seo_score: float | None
    seo_grade: str | None
    technologies: list[str]


@dataclass(frozen=True, slots=True)
class FacetValue:
    """A facet bucket: a value and how many matches carry it."""

    value: str
    count: int


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A page of search results plus facet counts and the total."""

    items: list[SearchResultItem]
    facets: dict[str, list[FacetValue]]
    total: int
    page: int
    page_size: int
