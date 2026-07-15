"""Pure query compilation and validation.

Turns a :class:`SearchQuery` into a validated, adapter-agnostic
:class:`CompiledQuery`. This is the single place filter semantics live, so it is
unit-tested without any database and shared by every search adapter.

Filter combination rules:
    * multiple values within one field  -> OR   (e.g. technology in [A, B])
    * different fields                   -> AND  (e.g. industry AND country)
    * free text                          -> ranking + an implicit AND match
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from bise.application.dto.search_dto import Filter, FilterOp, SearchQuery, SortSpec
from bise.application.errors import ApplicationError


class FieldKind(StrEnum):
    """How a field is stored and matched by adapters."""

    TEXT = "text"  # string column: EQ / IN
    NUMBER = "number"  # numeric column: GTE / LTE / EQ
    BOOL = "bool"  # boolean column: IS_TRUE / EQ
    LIST = "list"  # multi-valued (e.g. technologies): CONTAINS


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """Declares a filterable field and its permitted operators."""

    kind: FieldKind
    ops: frozenset[FilterOp]


_TEXT_OPS = frozenset({FilterOp.EQ, FilterOp.IN})
_NUMBER_OPS = frozenset({FilterOp.GTE, FilterOp.LTE, FilterOp.EQ, FilterOp.BETWEEN})
_BOOL_OPS = frozenset({FilterOp.IS_TRUE, FilterOp.EQ})
_LIST_OPS = frozenset({FilterOp.CONTAINS})

# The closed vocabulary of filterable fields (prevents injection and keeps every
# adapter implementable). Text fields accept IN for Sales-Navigator-style
# multi-select; number fields accept BETWEEN for range inputs.
FIELD_SPECS: dict[str, FieldSpec] = {
    "industry": FieldSpec(FieldKind.TEXT, _TEXT_OPS),
    "country": FieldSpec(FieldKind.TEXT, _TEXT_OPS),
    "state": FieldSpec(FieldKind.TEXT, _TEXT_OPS),
    "city": FieldSpec(FieldKind.TEXT, _TEXT_OPS),
    "size_bucket": FieldSpec(FieldKind.TEXT, _TEXT_OPS),
    "seo_grade": FieldSpec(FieldKind.TEXT, _TEXT_OPS),
    "seo_score": FieldSpec(FieldKind.NUMBER, _NUMBER_OPS),
    "founded_year": FieldSpec(FieldKind.NUMBER, _NUMBER_OPS),
    "employee_count": FieldSpec(FieldKind.NUMBER, _NUMBER_OPS),
    "technology": FieldSpec(FieldKind.LIST, _LIST_OPS),
    "role": FieldSpec(FieldKind.LIST, _LIST_OPS),
    "has_ssl": FieldSpec(FieldKind.BOOL, _BOOL_OPS),
    "has_contact_page": FieldSpec(FieldKind.BOOL, _BOOL_OPS),
    "has_careers_page": FieldSpec(FieldKind.BOOL, _BOOL_OPS),
    "has_blog": FieldSpec(FieldKind.BOOL, _BOOL_OPS),
    "has_privacy": FieldSpec(FieldKind.BOOL, _BOOL_OPS),
    "has_terms": FieldSpec(FieldKind.BOOL, _BOOL_OPS),
}

_SORT_FIELDS = frozenset({"relevance", "seo_score", "name", "recency"})
_MAX_PAGE_SIZE = 200


@dataclass(frozen=True, slots=True)
class Predicate:
    """A validated, normalized filter ready for an adapter to render."""

    field: str
    kind: FieldKind
    op: FilterOp
    values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompiledQuery:
    """A validated search request; the sole input to a search adapter."""

    text: str | None
    predicates: tuple[Predicate, ...]
    facets: tuple[str, ...]
    sort: SortSpec
    page: int
    page_size: int


def _validate_filter(f: Filter) -> Predicate:
    spec = FIELD_SPECS.get(f.field)
    if spec is None:
        raise ApplicationError(f"Unknown filter field: {f.field!r}")
    if f.op not in spec.ops:
        raise ApplicationError(f"Operator {f.op!r} not allowed on field {f.field!r}")

    if f.op in (FilterOp.IN, FilterOp.CONTAINS):
        if not f.values:
            raise ApplicationError(f"Filter on {f.field!r} requires at least one value")
    elif f.op is FilterOp.IS_TRUE:
        pass
    elif f.op is FilterOp.BETWEEN:
        if len(f.values) != 2:
            raise ApplicationError(
                f"Operator 'between' on {f.field!r} requires exactly two values (min, max)"
            )
        lo, hi = _as_number(f.field, f.values[0]), _as_number(f.field, f.values[1])
        if lo > hi:
            raise ApplicationError(f"Range on {f.field!r} requires min <= max")
    elif len(f.values) != 1:
        raise ApplicationError(f"Operator {f.op!r} on {f.field!r} requires exactly one value")

    # Numeric single-value operators must carry a parseable number.
    if spec.kind is FieldKind.NUMBER and f.op in (FilterOp.GTE, FilterOp.LTE, FilterOp.EQ):
        _as_number(f.field, f.values[0])

    return Predicate(field=f.field, kind=spec.kind, op=f.op, values=tuple(f.values))


def _as_number(field: str, value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ApplicationError(
            f"Filter on {field!r} requires a numeric value, got {value!r}"
        ) from None


def compile_query(query: SearchQuery) -> CompiledQuery:
    """Validate and normalize a search query. Raises on invalid fields/operators."""
    if query.page < 1:
        raise ApplicationError("page must be >= 1")
    if not 1 <= query.page_size <= _MAX_PAGE_SIZE:
        raise ApplicationError(f"page_size must be within [1, {_MAX_PAGE_SIZE}]")
    if query.sort.field not in _SORT_FIELDS:
        raise ApplicationError(f"Unknown sort field: {query.sort.field!r}")
    for facet in query.facets:
        if facet not in FIELD_SPECS:
            raise ApplicationError(f"Unknown facet field: {facet!r}")

    text = query.text.strip() if query.text and query.text.strip() else None
    predicates = tuple(_validate_filter(f) for f in query.filters)
    return CompiledQuery(
        text=text,
        predicates=predicates,
        facets=query.facets,
        sort=query.sort,
        page=query.page,
        page_size=query.page_size,
    )
