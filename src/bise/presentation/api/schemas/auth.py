"""Request/response schemas for the auth API (workspaces, API keys)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from bise.application.dto.auth_dto import ApiKeyDTO, CreatedApiKeyDTO, WorkspaceDTO


class CreateWorkspaceRequest(BaseModel):
    """Request body for ``POST /workspaces``."""

    name: str = Field(..., min_length=1, examples=["Acme Sales"])


class WorkspaceResponse(BaseModel):
    """A workspace."""

    id: int | None
    name: str
    slug: str
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: WorkspaceDTO) -> WorkspaceResponse:
        return cls(id=dto.id, name=dto.name, slug=dto.slug, created_at=dto.created_at)


class CreateApiKeyRequest(BaseModel):
    """Request body for ``POST /api-keys``."""

    name: str = Field(..., min_length=1, examples=["CI pipeline"])


class ApiKeyResponse(BaseModel):
    """An API key's metadata (never the secret)."""

    id: int | None
    workspace_id: int
    name: str
    prefix: str
    revoked: bool
    last_used_at: datetime | None
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: ApiKeyDTO) -> ApiKeyResponse:
        return cls(
            id=dto.id,
            workspace_id=dto.workspace_id,
            name=dto.name,
            prefix=dto.prefix,
            revoked=dto.revoked,
            last_used_at=dto.last_used_at,
            created_at=dto.created_at,
        )


class CreatedApiKeyResponse(BaseModel):
    """A newly created key: metadata plus the raw secret, shown exactly once."""

    api_key: ApiKeyResponse
    secret: str = Field(..., description="Store this now — it is never shown again")

    @classmethod
    def from_dto(cls, dto: CreatedApiKeyDTO) -> CreatedApiKeyResponse:
        return cls(api_key=ApiKeyResponse.from_dto(dto.api_key), secret=dto.secret)
