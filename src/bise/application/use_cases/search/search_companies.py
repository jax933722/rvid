"""Use case: execute a company search."""

from __future__ import annotations

from bise.application.dto.search_dto import SearchQuery, SearchResult
from bise.application.ports.search import SearchIndexPort
from bise.application.use_cases.search.compile_query import compile_query


class SearchCompanies:
    """Validate a search query and run it against the search index."""

    def __init__(self, search_index: SearchIndexPort) -> None:
        self._search_index = search_index

    def execute(self, query: SearchQuery) -> SearchResult:
        compiled = compile_query(query)  # validates fields/operators/paging
        return self._search_index.search(compiled)
