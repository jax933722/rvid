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
