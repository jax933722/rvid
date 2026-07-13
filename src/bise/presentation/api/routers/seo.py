"""SEO API — scan and read a company's SEO profile."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from bise.application.use_cases.enrichment.get_company_seo import GetCompanySeo
from bise.application.use_cases.enrichment.run_seo_scan import RunSeoScan
from bise.presentation.api.dependencies import get_get_company_seo, get_run_seo_scan
from bise.presentation.api.schemas.seo import SeoProfileResponse

router = APIRouter(tags=["seo"])


@router.get(
    "/companies/{company_id}/seo",
    response_model=SeoProfileResponse,
    summary="Get a company's SEO profile",
)
async def get_company_seo(
    company_id: int,
    use_case: Annotated[GetCompanySeo, Depends(get_get_company_seo)],
) -> SeoProfileResponse:
    """Return the company's stored SEO profile, or 404 if it hasn't been scanned."""
    return SeoProfileResponse.from_dto(use_case.execute(company_id))


@router.post(
    "/companies/{company_id}/seo/scan",
    response_model=SeoProfileResponse,
    summary="Run an SEO scan for a company",
)
async def scan_company_seo(
    company_id: int,
    use_case: Annotated[RunSeoScan, Depends(get_run_seo_scan)],
) -> SeoProfileResponse:
    """Analyze the company's stored homepage and persist a scored SEO profile.

    Runs locally over already-crawled content (no network), so it responds
    synchronously with the computed profile.
    """
    return SeoProfileResponse.from_dto(use_case.execute(company_id))
