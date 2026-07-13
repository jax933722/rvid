"""Search index port — the swap seam for the search backend.

A portable SQL adapter implements this now (SQLite dev / PostgreSQL prod); an
OpenSearch adapter can implement the same interface later. Business logic depends
only on this port and never learns which engine answered.
"""

from __future__ import annotations

from typing import Protocol

from bise.application.dto.search_dto import SearchResult
from bise.application.use_cases.search.compile_query import CompiledQuery
from bise.domain.entities.search_document import SearchDocument


class SearchIndexPort(Protocol):
    """Maintains and queries the searchable projection of companies."""

    def upsert(self, document: SearchDocument) -> None:
        """Insert or replace a company's search document."""
        ...

    def search(self, query: CompiledQuery) -> SearchResult:
        """Execute a validated query and return ranked results with facets."""
        ...
