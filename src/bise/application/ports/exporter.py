"""Exporter port — serialize tabular rows into a downloadable format.

Each concrete exporter (CSV, JSON, XLSX) renders the same row/column shape, so
the export use cases stay format-agnostic and new formats drop in behind this
port without touching business logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol


class ExporterPort(Protocol):
    """Renders rows + an ordered column list into bytes for a single format."""

    media_type: str
    extension: str

    def serialize(
        self, rows: Sequence[Mapping[str, object]], columns: Sequence[str]
    ) -> bytes:
        """Serialize the given rows (in ``columns`` order) to bytes."""
        ...
