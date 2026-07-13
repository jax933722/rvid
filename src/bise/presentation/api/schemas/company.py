"""Request/response schemas for the companies API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from bise.application.dto.company_dto import (
    CompanyDTO,
    CreateCompanyCommand,
    NewDomainDTO,
)


class NewDomainRequest(BaseModel):
    """A website domain to attach to a company on creation."""

    hostname: str = Field(..., examples=["acme.com"])
    is_primary: bool = False


class CreateCompanyRequest(BaseModel):
    """Request body for ``POST /companies``."""

    display_name: str = Field(..., min_length=1, examples=["Acme Dental"])
    legal_name: str | None = Field(default=None, examples=["Acme Dental Pty Ltd"])
    industry: str | None = Field(default=None, examples=["Dentistry"])
    size_bucket: str | None = Field(default=None, examples=["10-50"])
    domains: list[NewDomainRequest] = Field(default_factory=list)

    def to_command(self) -> CreateCompanyCommand:
        """Map the validated request into an application command."""
        return CreateCompanyCommand(
            display_name=self.display_name,
            legal_name=self.legal_name,
            industry=self.industry,
            size_bucket=self.size_bucket,
            domains=tuple(
                NewDomainDTO(hostname=d.hostname, is_primary=d.is_primary) for d in self.domains
            ),
        )


class DomainResponse(BaseModel):
    """A persisted website domain."""

    id: int | None
    hostname: str
    is_primary: bool
    crawl_status: str


class CompanyResponse(BaseModel):
    """A company detail/summary view."""

    id: int | None
    display_name: str
    legal_name: str | None
    status: str
    industry: str | None
    size_bucket: str | None
    domains: list[DomainResponse]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: CompanyDTO) -> CompanyResponse:
        """Build the response schema from an application DTO."""
        return cls(
            id=dto.id,
            display_name=dto.display_name,
            legal_name=dto.legal_name,
            status=dto.status,
            industry=dto.industry,
            size_bucket=dto.size_bucket,
            domains=[
                DomainResponse(
                    id=d.id,
                    hostname=d.hostname,
                    is_primary=d.is_primary,
                    crawl_status=d.crawl_status,
                )
                for d in dto.domains
            ],
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
