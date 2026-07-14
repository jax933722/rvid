"""Use case: export the members of a company list to a downloadable file."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.export_dto import ExportResult
from bise.application.errors import NotFoundError
from bise.application.export.rows import EXPORT_COLUMNS, company_to_row
from bise.application.mappers import company_to_dto
from bise.application.ports.exporter import ExporterPort
from bise.application.ports.unit_of_work import UnitOfWork

logger = get_logger(__name__)


class ExportListMembers:
    """Serialize the companies in a list with the given exporter."""

    def __init__(self, uow: UnitOfWork, exporter: ExporterPort) -> None:
        self._uow = uow
        self._exporter = exporter

    def execute(self, workspace_id: int, list_id: int) -> ExportResult:
        with self._uow as uow:
            company_list = uow.company_lists.get(workspace_id, list_id)
            if company_list is None:
                raise NotFoundError(f"List not found: {list_id}")
            members = uow.company_lists.list_members(list_id)
            rows = [company_to_row(company_to_dto(c)) for c in members]

        content = self._exporter.serialize(rows, EXPORT_COLUMNS)
        logger.info("export.list", list_id=list_id, rows=len(rows), fmt=self._exporter.extension)
        return ExportResult(
            content=content,
            media_type=self._exporter.media_type,
            filename=f"bise-list-{list_id}.{self._exporter.extension}",
        )
