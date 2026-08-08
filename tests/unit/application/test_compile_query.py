"""Unit tests for the pure search-query compiler."""

from __future__ import annotations

import pytest

from bise.application.dto.search_dto import Filter, FilterOp, SearchQuery, SortSpec
from bise.application.errors import ApplicationError
from bise.application.use_cases.search.compile_query import FieldKind, compile_query


def test_valid_query_compiles() -> None:
    query = SearchQuery(
        text="  dentist  ",
        filters=(
            Filter("industry", FilterOp.EQ, ("Dentistry",)),
            Filter("technology", FilterOp.CONTAINS, ("WordPress", "Shopify")),
            Filter("seo_score", FilterOp.LTE, ("50",)),
            Filter("has_contact_page", FilterOp.IS_TRUE),
        ),
        facets=("industry", "technology"),
    )
    compiled = compile_query(query)
    assert compiled.text == "dentist"  # trimmed
    assert len(compiled.predicates) == 4
    tech = next(p for p in compiled.predicates if p.field == "technology")
    assert tech.kind is FieldKind.LIST
    assert tech.values == ("WordPress", "Shopify")


def test_unknown_field_rejected() -> None:
    with pytest.raises(ApplicationError, match="Unknown filter field"):
        compile_query(SearchQuery(filters=(Filter("hacker", FilterOp.EQ, ("x",)),)))


def test_illegal_operator_rejected() -> None:
    # seo_score is numeric; CONTAINS is not allowed.
    with pytest.raises(ApplicationError, match="not allowed"):
        compile_query(SearchQuery(filters=(Filter("seo_score", FilterOp.CONTAINS, ("1",)),)))


def test_in_requires_values() -> None:
    with pytest.raises(ApplicationError, match="requires at least one value"):
        compile_query(SearchQuery(filters=(Filter("industry", FilterOp.IN, ()),)))


def test_unknown_sort_and_facet_rejected() -> None:
    with pytest.raises(ApplicationError, match="Unknown sort field"):
        compile_query(SearchQuery(sort=SortSpec(field="bogus")))
    with pytest.raises(ApplicationError, match="Unknown facet field"):
        compile_query(SearchQuery(facets=("bogus",)))


def test_paging_bounds() -> None:
    with pytest.raises(ApplicationError):
        compile_query(SearchQuery(page=0))
    with pytest.raises(ApplicationError):
        compile_query(SearchQuery(page_size=9999))


def test_empty_text_becomes_none() -> None:
    assert compile_query(SearchQuery(text="   ")).text is None


def test_between_compiles_on_number_field() -> None:
    compiled = compile_query(
        SearchQuery(filters=(Filter("founded_year", FilterOp.BETWEEN, ("2000", "2020")),))
    )
    pred = compiled.predicates[0]
    assert pred.kind is FieldKind.NUMBER
    assert pred.op is FilterOp.BETWEEN
    assert pred.values == ("2000", "2020")


def test_between_requires_two_values() -> None:
    with pytest.raises(ApplicationError, match="exactly two values"):
        compile_query(SearchQuery(filters=(Filter("employee_count", FilterOp.BETWEEN, ("5",)),)))


def test_between_rejects_min_greater_than_max() -> None:
    with pytest.raises(ApplicationError, match="min <= max"):
        compile_query(
            SearchQuery(filters=(Filter("founded_year", FilterOp.BETWEEN, ("2020", "2000")),))
        )


def test_between_not_allowed_on_text_field() -> None:
    with pytest.raises(ApplicationError, match="not allowed"):
        compile_query(SearchQuery(filters=(Filter("industry", FilterOp.BETWEEN, ("a", "b")),)))


def test_numeric_field_rejects_non_number() -> None:
    with pytest.raises(ApplicationError, match="numeric value"):
        compile_query(SearchQuery(filters=(Filter("employee_count", FilterOp.GTE, ("many",)),)))


def test_multi_select_industry_via_in() -> None:
    compiled = compile_query(
        SearchQuery(filters=(Filter("city", FilterOp.IN, ("Sydney", "Melbourne")),))
    )
    assert compiled.predicates[0].values == ("Sydney", "Melbourne")
