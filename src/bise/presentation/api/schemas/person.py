"""Response schema for people extracted from company websites."""

from __future__ import annotations

from pydantic import BaseModel

from bise.application.dto.person_dto import PersonDTO


class PersonResponse(BaseModel):
    """A person listed on a company's public site."""

    id: int | None
    company_id: int
    name: str
    title: str | None
    role_category: str
    email: str | None
    # "published" (found on site), "guessed" (inferred pattern, unverified), or "none".
    email_status: str
    source_url: str | None

    @classmethod
    def from_dto(cls, dto: PersonDTO) -> PersonResponse:
        return cls(
            id=dto.id,
            company_id=dto.company_id,
            name=dto.name,
            title=dto.title,
            role_category=dto.role_category,
            email=dto.email,
            email_status=dto.email_status,
            source_url=dto.source_url,
        )
