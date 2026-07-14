"""Workspace API — saved searches, company lists, and tags."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, status

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
from bise.presentation.api.dependencies import (
    WorkspaceDep,
    get_add_company_tag,
    get_add_company_to_list,
    get_create_company_list,
    get_delete_company_list,
    get_delete_saved_search,
    get_list_company_lists,
    get_list_company_tags,
    get_list_list_members,
    get_list_saved_searches,
    get_remove_company_from_list,
    get_remove_company_tag,
    get_save_search,
)
from bise.presentation.api.schemas.company import CompanyResponse
from bise.presentation.api.schemas.workspace import (
    AddTagRequest,
    AddToListRequest,
    CompanyListResponse,
    CompanyTagResponse,
    CreateListRequest,
    SavedSearchResponse,
    SaveSearchRequest,
)

router = APIRouter(tags=["workspace"])


# --- saved searches --------------------------------------------------------
@router.post(
    "/saved-searches",
    response_model=SavedSearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a Prospector search",
)
async def save_search(
    body: SaveSearchRequest,
    workspace_id: WorkspaceDep,
    use_case: Annotated[SaveSearch, Depends(get_save_search)],
) -> SavedSearchResponse:
    dto = use_case.execute(workspace_id, name=body.name, query_json=json.dumps(body.query))
    return SavedSearchResponse.from_dto(dto)


@router.get(
    "/saved-searches",
    response_model=list[SavedSearchResponse],
    summary="List saved searches",
)
async def list_saved_searches(
    workspace_id: WorkspaceDep,
    use_case: Annotated[ListSavedSearches, Depends(get_list_saved_searches)],
) -> list[SavedSearchResponse]:
    return [SavedSearchResponse.from_dto(s) for s in use_case.execute(workspace_id)]


@router.delete(
    "/saved-searches/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved search",
)
async def delete_saved_search(
    search_id: int,
    workspace_id: WorkspaceDep,
    use_case: Annotated[DeleteSavedSearch, Depends(get_delete_saved_search)],
) -> None:
    use_case.execute(workspace_id, search_id)


# --- lists -----------------------------------------------------------------
@router.post(
    "/lists",
    response_model=CompanyListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a company list",
)
async def create_list(
    body: CreateListRequest,
    workspace_id: WorkspaceDep,
    use_case: Annotated[CreateCompanyList, Depends(get_create_company_list)],
) -> CompanyListResponse:
    return CompanyListResponse.from_dto(use_case.execute(workspace_id, body.name, body.description))


@router.get("/lists", response_model=list[CompanyListResponse], summary="List company lists")
async def list_lists(
    workspace_id: WorkspaceDep,
    use_case: Annotated[ListCompanyLists, Depends(get_list_company_lists)],
) -> list[CompanyListResponse]:
    return [CompanyListResponse.from_dto(cl) for cl in use_case.execute(workspace_id)]


@router.delete(
    "/lists/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a company list",
)
async def delete_list(
    list_id: int,
    workspace_id: WorkspaceDep,
    use_case: Annotated[DeleteCompanyList, Depends(get_delete_company_list)],
) -> None:
    use_case.execute(workspace_id, list_id)


@router.get(
    "/lists/{list_id}/companies",
    response_model=list[CompanyResponse],
    summary="List companies in a list",
)
async def list_members(
    list_id: int,
    workspace_id: WorkspaceDep,
    use_case: Annotated[ListListMembers, Depends(get_list_list_members)],
) -> list[CompanyResponse]:
    return [CompanyResponse.from_dto(c) for c in use_case.execute(workspace_id, list_id)]


@router.post(
    "/lists/{list_id}/companies",
    response_model=CompanyListResponse,
    summary="Add a company to a list",
)
async def add_to_list(
    list_id: int,
    body: AddToListRequest,
    workspace_id: WorkspaceDep,
    use_case: Annotated[AddCompanyToList, Depends(get_add_company_to_list)],
) -> CompanyListResponse:
    return CompanyListResponse.from_dto(use_case.execute(workspace_id, list_id, body.company_id))


@router.delete(
    "/lists/{list_id}/companies/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a company from a list",
)
async def remove_from_list(
    list_id: int,
    company_id: int,
    workspace_id: WorkspaceDep,
    use_case: Annotated[RemoveCompanyFromList, Depends(get_remove_company_from_list)],
) -> None:
    use_case.execute(workspace_id, list_id, company_id)


# --- tags ------------------------------------------------------------------
@router.get(
    "/companies/{company_id}/tags",
    response_model=list[CompanyTagResponse],
    summary="List a company's tags",
)
async def list_tags(
    company_id: int,
    workspace_id: WorkspaceDep,
    use_case: Annotated[ListCompanyTags, Depends(get_list_company_tags)],
) -> list[CompanyTagResponse]:
    return [CompanyTagResponse.from_dto(t) for t in use_case.execute(workspace_id, company_id)]


@router.post(
    "/companies/{company_id}/tags",
    response_model=CompanyTagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tag a company",
)
async def add_tag(
    company_id: int,
    body: AddTagRequest,
    workspace_id: WorkspaceDep,
    use_case: Annotated[AddCompanyTag, Depends(get_add_company_tag)],
) -> CompanyTagResponse:
    return CompanyTagResponse.from_dto(use_case.execute(workspace_id, company_id, body.label))


@router.delete(
    "/companies/{company_id}/tags/{label}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a tag from a company",
)
async def remove_tag(
    company_id: int,
    label: str,
    workspace_id: WorkspaceDep,
    use_case: Annotated[RemoveCompanyTag, Depends(get_remove_company_tag)],
) -> None:
    use_case.execute(workspace_id, company_id, label)
