"""Companies API — create, fetch, and list companies."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from bise.application.use_cases.companies.create_company import CreateCompany
from bise.application.use_cases.companies.get_company import GetCompany
from bise.application.use_cases.companies.list_companies import ListCompanies
from bise.application.use_cases.enrichment.list_company_people import ListCompanyPeople
from bise.presentation.api.dependencies import (
    get_create_company,
    get_get_company,
    get_list_companies,
    get_list_company_people,
)
from bise.presentation.api.schemas.common import PageResponse
from bise.presentation.api.schemas.company import CompanyResponse, CreateCompanyRequest
from bise.presentation.api.schemas.person import PersonResponse
from bise.shared.pagination import PageRequest

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a company",
)
async def create_company(
    body: CreateCompanyRequest,
    use_case: Annotated[CreateCompany, Depends(get_create_company)],
) -> CompanyResponse:
    """Create a company, optionally attaching one or more website domains."""
    dto = use_case.execute(body.to_command())
    return CompanyResponse.from_dto(dto)


@router.get(
    "",
    response_model=PageResponse[CompanyResponse],
    summary="List companies",
)
async def list_companies(
    use_case: Annotated[ListCompanies, Depends(get_list_companies)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 25,
) -> PageResponse[CompanyResponse]:
    """Return a paginated list of companies, newest first."""
    result = use_case.execute(PageRequest(page=page, page_size=page_size))
    return PageResponse[CompanyResponse](
        items=[CompanyResponse.from_dto(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get a company by id",
)
async def get_company(
    company_id: int,
    use_case: Annotated[GetCompany, Depends(get_get_company)],
) -> CompanyResponse:
    """Return a single company's full profile, or 404 if it does not exist."""
    dto = use_case.execute(company_id)
    return CompanyResponse.from_dto(dto)


@router.get(
    "/{company_id}/people",
    response_model=list[PersonResponse],
    summary="List people published on a company's site",
)
async def list_company_people(
    company_id: int,
    use_case: Annotated[ListCompanyPeople, Depends(get_list_company_people)],
) -> list[PersonResponse]:
    """Return the company's team members (name, role, and public/guessed email)."""
    return [PersonResponse.from_dto(p) for p in use_case.execute(company_id)]
