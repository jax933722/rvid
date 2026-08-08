"""DTOs for the export feature."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ExportFormat(StrEnum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"


@dataclass(frozen=True, slots=True)
class ExportResult:
    """A rendered export payload ready to stream back to the caller."""

    content: bytes
    media_type: str
    filename: str
