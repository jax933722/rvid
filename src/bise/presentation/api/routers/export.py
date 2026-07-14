"""Export API — download search results or list members as CSV / JSON / XLSX."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response

from bise.application.dto.export_dto import ExportFormat, ExportResult
from bise.presentation.api.dependencies import ContainerDep
from bise.presentation.api.schemas.search import SearchRequest

router = APIRouter(tags=["export"])

FormatQuery = Annotated[ExportFormat, Query(alias="format", description="csv | json | xlsx")]


def _as_response(result: ExportResult) -> Response:
    return Response(
        content=result.content,
        media_type=result.media_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )


@router.post("/export/search", summary="Export search results")
async def export_search(
    body: SearchRequest,
    container: ContainerDep,
    fmt: FormatQuery = ExportFormat.CSV,
) -> Response:
    """Run the given Prospector query and download every match as a file."""
    result = container.export_search_results(fmt).execute(body.to_query())
    return _as_response(result)


@router.get("/export/lists/{list_id}", summary="Export the companies in a list")
async def export_list(
    list_id: int,
    container: ContainerDep,
    fmt: FormatQuery = ExportFormat.CSV,
) -> Response:
    """Download all companies belonging to a list as a file."""
    result = container.export_list_members(fmt).execute(list_id)
    return _as_response(result)
