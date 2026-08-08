"""Use case: read the lead inbox — freshest leads first, optionally per campaign."""

from __future__ import annotations

from bise.application.dto.lead_dto import LeadDTO
from bise.application.mappers import lead_to_dto
from bise.application.ports.unit_of_work import UnitOfWork


class ListLeads:
    """Return the most recent leads with their company, newest first."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, limit: int = 100, campaign_id: int | None = None) -> list[LeadDTO]:
        with self._uow as uow:
            rows = uow.leads.list_recent(limit=limit, campaign_id=campaign_id)
            return [lead_to_dto(lead, company) for lead, company in rows]
