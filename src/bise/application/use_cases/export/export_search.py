"""Use case: export a full search result set to a downloadable file.

Unlike the paged search endpoint, an export gathers every matching row (up to a
safety cap) by walking the pages, then hands them to a format-specific exporter.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from config.logging import get_logger

from bise.application.dto.export_dto import ExportResult
from bise.application.dto.search_dto import SearchQuery
from bise.application.export.rows import EXPORT_COLUMNS, search_item_to_row
from bise.application.ports.exporter import ExporterPort
from bise.application.ports.search import SearchIndexPort
from bise.application.use_cases.search.compile_query import compile_query

logger = get_logger(__name__)

_PAGE_SIZE = 200
_MAX_ROWS = 5000


class ExportSearchResults:
    """Run a search and serialize all matching companies with the given exporter."""

    def __init__(self, search_index: SearchIndexPort, exporter: ExporterPort) -> None:
        self._search_index = search_index
        self._exporter = exporter

    def execute(self, query: SearchQuery) -> ExportResult:
        rows: list[Mapping[str, object]] = []
        page = 1
        while len(rows) < _MAX_ROWS:
            compiled = compile_query(replace(query, page=page, page_size=_PAGE_SIZE))
            result = self._search_index.search(compiled)
            rows.extend(search_item_to_row(item) for item in result.items)
            if page * _PAGE_SIZE >= result.total or not result.items:
                break
            page += 1

        content = self._exporter.serialize(rows[:_MAX_ROWS], EXPORT_COLUMNS)
        logger.info("export.search", rows=len(rows), fmt=self._exporter.extension)
        return ExportResult(
            content=content,
            media_type=self._exporter.media_type,
            filename=f"bise-search.{self._exporter.extension}",
        )
