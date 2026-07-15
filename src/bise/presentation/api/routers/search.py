"""Search API — faceted multi-filter company search and reindexing.

Search responses are cached with a short TTL (shared public data), keyed by the
normalized request body. Any write that changes the index — reindex here, or the
enrich/enqueue-drain endpoints — clears the cache so results are never stale.
"""

from __future__ import annotations

import hashlib
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from bise.application.use_cases.search.rebuild_search_document import RebuildSearchDocument
from bise.application.use_cases.search.search_companies import SearchCompanies
from bise.presentation.api.dependencies import (
    ContainerDep,
    get_rebuild_search_document,
    get_search_companies,
)
from bise.presentation.api.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])

_JSON = "application/json"


def _cache_key(body: SearchRequest) -> str:
    payload = json.dumps(body.model_dump(), sort_keys=True, default=str)
    return "search:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


@router.post("/search", response_model=SearchResponse, summary="Search companies")
async def search(
    body: SearchRequest,
    container: ContainerDep,
    use_case: Annotated[SearchCompanies, Depends(get_search_companies)],
) -> Response:
    """Search companies with free text + combinable filters, facets, and paging.

    Filters combine as OR within a field and AND across fields (e.g.
    ``technology in [WordPress] AND industry = Dentistry AND seo_score < 50``).
    """
    caching = container.settings.cache_enabled
    cache = container.search_cache()
    key = _cache_key(body) if caching else ""

    if caching:
        hit = cache.get(key)
        if hit is not None:
            return Response(content=hit, media_type=_JSON, headers={"X-Cache": "HIT"})

    result = use_case.execute(body.to_query())
    payload = SearchResponse.from_result(result).model_dump_json().encode("utf-8")
    if caching:
        cache.set(key, payload, container.settings.cache_ttl_seconds)
    return Response(content=payload, media_type=_JSON, headers={"X-Cache": "MISS"})


@router.post(
    "/companies/{company_id}/index",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Rebuild a company's search document",
)
async def reindex_company(
    company_id: int,
    container: ContainerDep,
    use_case: Annotated[RebuildSearchDocument, Depends(get_rebuild_search_document)],
) -> dict[str, str]:
    """Rebuild the company's searchable projection from its enriched data."""
    use_case.execute(company_id)
    container.search_cache().clear()  # results changed — drop stale cache
    return {"status": "indexed"}
