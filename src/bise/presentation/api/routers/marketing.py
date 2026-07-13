"""Marketing API — detect and read a company's marketing tooling."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from bise.application.use_cases.enrichment.detect_marketing import DetectMarketing
from bise.application.use_cases.enrichment.list_company_marketing import ListCompanyMarketing
from bise.presentation.api.dependencies import (
    get_detect_marketing,
    get_list_company_marketing,
)
from bise.presentation.api.schemas.marketing import MarketingSignalResponse

router = APIRouter(tags=["marketing"])


@router.get(
    "/companies/{company_id}/marketing",
    response_model=list[MarketingSignalResponse],
    summary="List marketing tools detected for a company",
)
async def list_company_marketing(
    company_id: int,
    use_case: Annotated[ListCompanyMarketing, Depends(get_list_company_marketing)],
) -> list[MarketingSignalResponse]:
    """Return the marketing tools detected on a company's website."""
    return [MarketingSignalResponse.from_dto(s) for s in use_case.execute(company_id)]


@router.post(
    "/companies/{company_id}/marketing/detect",
    response_model=list[MarketingSignalResponse],
    summary="Run marketing detection for a company",
)
async def detect_company_marketing(
    company_id: int,
    use_case: Annotated[DetectMarketing, Depends(get_detect_marketing)],
) -> list[MarketingSignalResponse]:
    """Detect marketing tools from the company's stored pages and persist the result.

    Runs locally over already-crawled pages (no network), so it responds
    synchronously with the detected tools.
    """
    return [MarketingSignalResponse.from_dto(s) for s in use_case.execute(company_id)]
