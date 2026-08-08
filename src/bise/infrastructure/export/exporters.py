"""CSV, JSON, and XLSX exporters (implement :class:`ExporterPort`).

All three share the same row/column contract. CSV and JSON use the standard
library; XLSX uses openpyxl (free, open-source). openpyxl is the only place its
untyped API is touched, keeping the ``Any`` boundary contained.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence

from openpyxl import Workbook

from bise.application.dto.export_dto import ExportFormat


def _cell(value: object) -> object:
    """Normalize a value for serialization (``None`` becomes an empty string)."""
    return "" if value is None else value


class CsvExporter:
    """Render rows as UTF-8 CSV (with a BOM so Excel opens it correctly)."""

    media_type = "text/csv"
    extension = "csv"

    def serialize(self, rows: Sequence[Mapping[str, object]], columns: Sequence[str]) -> bytes:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: _cell(row.get(c)) for c in columns})
        return buffer.getvalue().encode("utf-8-sig")


class JsonExporter:
    """Render rows as a pretty-printed JSON array of objects."""

    media_type = "application/json"
    extension = "json"

    def serialize(self, rows: Sequence[Mapping[str, object]], columns: Sequence[str]) -> bytes:
        payload = [{c: row.get(c) for c in columns} for row in rows]
        return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


class XlsxExporter:
    """Render rows as a single-sheet .xlsx workbook via openpyxl."""

    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    extension = "xlsx"

    def serialize(self, rows: Sequence[Mapping[str, object]], columns: Sequence[str]) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Companies"
        sheet.append(list(columns))
        for row in rows:
            sheet.append([_cell(row.get(c)) for c in columns])
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()


def build_exporter(fmt: ExportFormat) -> CsvExporter | JsonExporter | XlsxExporter:
    """Return the exporter for a format."""
    if fmt is ExportFormat.CSV:
        return CsvExporter()
    if fmt is ExportFormat.JSON:
        return JsonExporter()
    return XlsxExporter()
