"""Unit tests for workspace domain entities and their invariants."""

from __future__ import annotations

import pytest

from bise.domain.entities.company_list import CompanyList
from bise.domain.entities.company_tag import CompanyTag
from bise.domain.entities.saved_search import SavedSearch
from bise.domain.errors import InvalidValueError


def test_saved_search_requires_name_and_payload() -> None:
    with pytest.raises(InvalidValueError):
        SavedSearch(name="  ", query_json="{}")
    with pytest.raises(InvalidValueError):
        SavedSearch(name="ok", query_json="   ")


def test_saved_search_trims_name() -> None:
    assert SavedSearch(name="  Leads  ", query_json="{}").name == "Leads"


def test_company_list_requires_name() -> None:
    with pytest.raises(InvalidValueError):
        CompanyList(name="")


def test_company_list_normalizes_blank_description_to_none() -> None:
    assert CompanyList(name="A", description="   ").description is None
    assert CompanyList(name="A", description=" hot ").description == "hot"


def test_company_tag_normalizes_label() -> None:
    tag = CompanyTag(company_id=1, label="  Priority ")
    assert tag.label == "priority"


def test_company_tag_rejects_empty_label() -> None:
    with pytest.raises(InvalidValueError):
        CompanyTag(company_id=1, label="   ")
