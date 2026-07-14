"""Integration tests for workspace use cases against SQLite (via the container)."""

from __future__ import annotations

import pytest
from config.containers import Container

from bise.application.dto.company_dto import CreateCompanyCommand, NewDomainDTO
from bise.application.errors import NotFoundError
from bise.application.use_cases.workspace.lists import (
    AddCompanyToList,
    CreateCompanyList,
    DeleteCompanyList,
    ListCompanyLists,
    ListListMembers,
    RemoveCompanyFromList,
)
from bise.application.use_cases.workspace.saved_searches import (
    DeleteSavedSearch,
    ListSavedSearches,
    SaveSearch,
)
from bise.application.use_cases.workspace.tags import (
    AddCompanyTag,
    ListCompanyTags,
    RemoveCompanyTag,
)


def _company(container: Container, name: str, host: str) -> int:
    dto = container.create_company().execute(
        CreateCompanyCommand(
            display_name=name, domains=(NewDomainDTO(hostname=host, is_primary=True),)
        )
    )
    assert dto.id is not None
    return dto.id


# --- saved searches --------------------------------------------------------
def test_saved_search_crud(container: Container) -> None:
    saved = SaveSearch(container.unit_of_work()).execute("Sydney dentists", '{"text":"dentist"}')
    assert saved.id is not None

    listed = ListSavedSearches(container.unit_of_work()).execute()
    assert [s.name for s in listed] == ["Sydney dentists"]

    DeleteSavedSearch(container.unit_of_work()).execute(saved.id)
    assert ListSavedSearches(container.unit_of_work()).execute() == []


def test_delete_missing_saved_search_raises(container: Container) -> None:
    with pytest.raises(NotFoundError):
        DeleteSavedSearch(container.unit_of_work()).execute(999)


# --- lists -----------------------------------------------------------------
def test_list_membership_lifecycle(container: Container) -> None:
    acme = _company(container, "Acme", "acme.com")
    beta = _company(container, "Beta", "beta.com")
    lst = CreateCompanyList(container.unit_of_work()).execute("Q3 outreach", "warm leads")
    assert lst.id is not None and lst.member_count == 0

    add = AddCompanyToList(container.unit_of_work())
    updated = add.execute(lst.id, acme)
    assert updated.member_count == 1
    # Idempotent: adding the same company again does not double-count.
    assert add.execute(lst.id, acme).member_count == 1
    assert add.execute(lst.id, beta).member_count == 2

    members = ListListMembers(container.unit_of_work()).execute(lst.id)
    assert {m.display_name for m in members} == {"Acme", "Beta"}

    RemoveCompanyFromList(container.unit_of_work()).execute(lst.id, acme)
    after = ListCompanyLists(container.unit_of_work()).execute()
    assert after[0].member_count == 1

    DeleteCompanyList(container.unit_of_work()).execute(lst.id)
    assert ListCompanyLists(container.unit_of_work()).execute() == []


def test_add_to_missing_list_raises(container: Container) -> None:
    acme = _company(container, "Acme", "acme.com")
    with pytest.raises(NotFoundError):
        AddCompanyToList(container.unit_of_work()).execute(999, acme)


def test_add_missing_company_to_list_raises(container: Container) -> None:
    lst = CreateCompanyList(container.unit_of_work()).execute("L")
    assert lst.id is not None
    with pytest.raises(NotFoundError):
        AddCompanyToList(container.unit_of_work()).execute(lst.id, 999)


def test_members_of_missing_list_raises(container: Container) -> None:
    with pytest.raises(NotFoundError):
        ListListMembers(container.unit_of_work()).execute(999)


def test_delete_missing_list_raises(container: Container) -> None:
    with pytest.raises(NotFoundError):
        DeleteCompanyList(container.unit_of_work()).execute(999)


def test_remove_from_missing_list_raises(container: Container) -> None:
    with pytest.raises(NotFoundError):
        RemoveCompanyFromList(container.unit_of_work()).execute(999, 1)


# --- tags ------------------------------------------------------------------
def test_tag_lifecycle_and_normalization(container: Container) -> None:
    acme = _company(container, "Acme", "acme.com")
    add = AddCompanyTag(container.unit_of_work())
    add.execute(acme, "Priority")
    # Case-insensitive idempotency: "priority" collapses to the same tag.
    add.execute(acme, "priority")
    add.execute(acme, "contacted")

    tags = ListCompanyTags(container.unit_of_work()).execute(acme)
    assert [t.label for t in tags] == ["contacted", "priority"]  # ordered by label

    RemoveCompanyTag(container.unit_of_work()).execute(acme, "Priority")
    assert [t.label for t in ListCompanyTags(container.unit_of_work()).execute(acme)] == [
        "contacted"
    ]


def test_tag_missing_company_raises(container: Container) -> None:
    with pytest.raises(NotFoundError):
        AddCompanyTag(container.unit_of_work()).execute(999, "x")
