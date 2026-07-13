"""Search API — faceted multi-filter company search and reindexing."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from bise.application.use_cases.search.rebuild_search_document import RebuildSearchDocument
from bise.application.use_cases.search.search_companies import SearchCompanies
from bise.presentation.api.dependencies import (
    get_rebuild_search_document,
    get_search_companies,
)
from bise.presentation.api.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse, summary="Search companies")
async def search(
    body: SearchRequest,
    use_case: Annotated[SearchCompanies, Depends(get_search_companies)],
) -> SearchResponse:
    """Search companies with free text + combinable filters, facets, and paging.

    Filters combine as OR within a field and AND across fields (e.g.
    ``technology in [WordPress] AND industry = Dentistry AND seo_score < 50``).
    """
    result = use_case.execute(body.to_query())
    return SearchResponse.from_result(result)


@router.post(
    "/companies/{company_id}/index",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Rebuild a company's search document",
)
async def reindex_company(
    company_id: int,
    use_case: Annotated[RebuildSearchDocument, Depends(get_rebuild_search_document)],
) -> dict[str, str]:
    """Rebuild the company's searchable projection from its enriched data."""
    use_case.execute(company_id)
    return {"status": "indexed"}
