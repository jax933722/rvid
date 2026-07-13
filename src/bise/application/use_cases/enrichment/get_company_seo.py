"""Use case: fetch a company's SEO profile."""

from __future__ import annotations

from bise.application.dto.seo_dto import SeoProfileDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import seo_profile_to_dto
from bise.application.ports.unit_of_work import UnitOfWork


class GetCompanySeo:
    """Return a company's SEO profile, or raise :class:`NotFoundError`."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, company_id: int) -> SeoProfileDTO:
        with self._uow as uow:
            if uow.companies.get(company_id) is None:
                raise NotFoundError(f"Company not found: {company_id}")
            profile = uow.seo_profiles.get_for_company(company_id)
        if profile is None:
            raise NotFoundError(f"No SEO profile for company {company_id}; run a scan first")
        return seo_profile_to_dto(profile)
