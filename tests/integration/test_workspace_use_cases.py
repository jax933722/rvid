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


def _workspace(container: Container, name: str = "Test Workspace") -> int:
    dto = container.create_workspace().execute(name)
    assert dto.id is not None
    return dto.id


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
    ws = _workspace(container)
    saved = SaveSearch(container.unit_of_work()).execute(
        ws, "Sydney dentists", '{"text":"dentist"}'
    )
    assert saved.id is not None

    listed = ListSavedSearches(container.unit_of_work()).execute(ws)
    assert [s.name for s in listed] == ["Sydney dentists"]

    DeleteSavedSearch(container.unit_of_work()).execute(ws, saved.id)
    assert ListSavedSearches(container.unit_of_work()).execute(ws) == []


def test_saved_search_is_workspace_isolated(container: Container) -> None:
    ws_a = _workspace(container, "Alpha")
    ws_b = _workspace(container, "Bravo")
    SaveSearch(container.unit_of_work()).execute(ws_a, "A search", "{}")
    # Workspace B cannot see A's saved searches.
    assert ListSavedSearches(container.unit_of_work()).execute(ws_b) == []


def test_delete_missing_saved_search_raises(container: Container) -> None:
    ws = _workspace(container)
    with pytest.raises(NotFoundError):
        DeleteSavedSearch(container.unit_of_work()).execute(ws, 999)


# --- lists -----------------------------------------------------------------
def test_list_membership_lifecycle(container: Container) -> None:
    ws = _workspace(container)
    acme = _company(container, "Acme", "acme.com")
    beta = _company(container, "Beta", "beta.com")
    lst = CreateCompanyList(container.unit_of_work()).execute(ws, "Q3 outreach", "warm leads")
    assert lst.id is not None and lst.member_count == 0

    add = AddCompanyToList(container.unit_of_work())
    updated = add.execute(ws, lst.id, acme)
    assert updated.member_count == 1
    assert add.execute(ws, lst.id, acme).member_count == 1  # idempotent
    assert add.execute(ws, lst.id, beta).member_count == 2

    members = ListListMembers(container.unit_of_work()).execute(ws, lst.id)
    assert {m.display_name for m in members} == {"Acme", "Beta"}

    RemoveCompanyFromList(container.unit_of_work()).execute(ws, lst.id, acme)
    after = ListCompanyLists(container.unit_of_work()).execute(ws)
    assert after[0].member_count == 1

    DeleteCompanyList(container.unit_of_work()).execute(ws, lst.id)
    assert ListCompanyLists(container.unit_of_work()).execute(ws) == []


def test_list_is_workspace_isolated(container: Container) -> None:
    ws_a = _workspace(container, "Alpha")
    ws_b = _workspace(container, "Bravo")
    lst = CreateCompanyList(container.unit_of_work()).execute(ws_a, "A list")
    assert lst.id is not None
    # Workspace B cannot see or fetch A's list.
    assert ListCompanyLists(container.unit_of_work()).execute(ws_b) == []
    with pytest.raises(NotFoundError):
        ListListMembers(container.unit_of_work()).execute(ws_b, lst.id)


def test_add_to_missing_list_raises(container: Container) -> None:
    ws = _workspace(container)
    acme = _company(container, "Acme", "acme.com")
    with pytest.raises(NotFoundError):
        AddCompanyToList(container.unit_of_work()).execute(ws, 999, acme)


def test_add_missing_company_to_list_raises(container: Container) -> None:
    ws = _workspace(container)
    lst = CreateCompanyList(container.unit_of_work()).execute(ws, "L")
    assert lst.id is not None
    with pytest.raises(NotFoundError):
        AddCompanyToList(container.unit_of_work()).execute(ws, lst.id, 999)


def test_members_of_missing_list_raises(container: Container) -> None:
    ws = _workspace(container)
    with pytest.raises(NotFoundError):
        ListListMembers(container.unit_of_work()).execute(ws, 999)


def test_delete_missing_list_raises(container: Container) -> None:
    ws = _workspace(container)
    with pytest.raises(NotFoundError):
        DeleteCompanyList(container.unit_of_work()).execute(ws, 999)


def test_remove_from_missing_list_raises(container: Container) -> None:
    ws = _workspace(container)
    with pytest.raises(NotFoundError):
        RemoveCompanyFromList(container.unit_of_work()).execute(ws, 999, 1)


# --- tags ------------------------------------------------------------------
def test_tag_lifecycle_and_normalization(container: Container) -> None:
    ws = _workspace(container)
    acme = _company(container, "Acme", "acme.com")
    add = AddCompanyTag(container.unit_of_work())
    add.execute(ws, acme, "Priority")
    add.execute(ws, acme, "priority")  # case-insensitive idempotency
    add.execute(ws, acme, "contacted")

    tags = ListCompanyTags(container.unit_of_work()).execute(ws, acme)
    assert [t.label for t in tags] == ["contacted", "priority"]  # ordered by label

    RemoveCompanyTag(container.unit_of_work()).execute(ws, acme, "Priority")
    assert [t.label for t in ListCompanyTags(container.unit_of_work()).execute(ws, acme)] == [
        "contacted"
    ]


def test_tags_are_workspace_isolated(container: Container) -> None:
    ws_a = _workspace(container, "Alpha")
    ws_b = _workspace(container, "Bravo")
    acme = _company(container, "Acme", "acme.com")
    AddCompanyTag(container.unit_of_work()).execute(ws_a, acme, "priority")
    # Same company, different workspace -> no tags visible.
    assert ListCompanyTags(container.unit_of_work()).execute(ws_b, acme) == []


def test_tag_missing_company_raises(container: Container) -> None:
    ws = _workspace(container)
    with pytest.raises(NotFoundError):
        AddCompanyTag(container.unit_of_work()).execute(ws, 999, "x")
