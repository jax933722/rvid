"""Technology API — catalog, detection, and per-company detections."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from bise.application.use_cases.enrichment.detect_technologies import DetectTechnologies
from bise.application.use_cases.enrichment.list_company_technologies import ListCompanyTechnologies
from bise.application.use_cases.enrichment.list_technologies import ListTechnologies
from bise.presentation.api.dependencies import (
    get_detect_technologies,
    get_list_company_technologies,
    get_list_technologies,
)
from bise.presentation.api.schemas.common import PageResponse
from bise.presentation.api.schemas.technology import (
    CompanyTechnologyResponse,
    TechnologyResponse,
)
from bise.shared.pagination import PageRequest

router = APIRouter(tags=["technologies"])


@router.get(
    "/technologies",
    response_model=PageResponse[TechnologyResponse],
    summary="List known technologies",
)
async def list_technologies(
    use_case: Annotated[ListTechnologies, Depends(get_list_technologies)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> PageResponse[TechnologyResponse]:
    """Return the catalog of detected technologies (a search-filter facet source)."""
    result = use_case.execute(PageRequest(page=page, page_size=page_size))
    return PageResponse[TechnologyResponse](
        items=[TechnologyResponse.from_dto(t) for t in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/companies/{company_id}/technologies",
    response_model=list[CompanyTechnologyResponse],
    summary="List technologies detected for a company",
)
async def list_company_technologies(
    company_id: int,
    use_case: Annotated[ListCompanyTechnologies, Depends(get_list_company_technologies)],
) -> list[CompanyTechnologyResponse]:
    """Return the technologies detected on a company's website."""
    return [CompanyTechnologyResponse.from_dto(t) for t in use_case.execute(company_id)]


@router.post(
    "/companies/{company_id}/technologies/detect",
    response_model=list[CompanyTechnologyResponse],
    summary="Run technology detection for a company",
)
async def detect_company_technologies(
    company_id: int,
    use_case: Annotated[DetectTechnologies, Depends(get_detect_technologies)],
) -> list[CompanyTechnologyResponse]:
    """Detect technologies from the company's stored pages and persist the result.

    Detection reads already-crawled pages and runs local rule matching (no
    network), so it responds synchronously with the detected technologies.
    """
    return [CompanyTechnologyResponse.from_dto(t) for t in use_case.execute(company_id)]
