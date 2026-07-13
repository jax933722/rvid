"""Discovery API — find businesses online and enrich them on demand."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from bise.application.use_cases.discovery.discover_businesses import DiscoverBusinesses
from bise.presentation.api.dependencies import ContainerDep, get_discover_businesses
from bise.presentation.api.schemas.discovery import (
    DiscoveredBusinessResponse,
    DiscoverRequest,
)
from bise.presentation.workers.enrich import enrich_company

router = APIRouter(tags=["discovery"])


@router.post(
    "/discover",
    response_model=list[DiscoveredBusinessResponse],
    summary="Discover businesses online",
)
async def discover(
    body: DiscoverRequest,
    use_case: Annotated[DiscoverBusinesses, Depends(get_discover_businesses)],
) -> list[DiscoveredBusinessResponse]:
    """Find businesses by category + location from OpenStreetMap (live), and save
    the ones that have a website as companies so they can be enriched."""
    results = use_case.execute(body.to_command())
    return [DiscoveredBusinessResponse.from_dto(r) for r in results]


@router.post(
    "/companies/{company_id}/enrich",
    summary="Crawl + fully enrich a company (on demand)",
)
async def enrich(company_id: int, container: ContainerDep) -> dict[str, str | int]:
    """Run the full pipeline for one company: crawl its site, detect technologies
    and marketing, scan SEO, and rebuild its search index. Performs live network
    I/O, so it runs synchronously for a single company."""
    enrich_company(container, company_id)
    return {"status": "enriched", "company_id": company_id}
