"""Auth API — workspaces, API keys, and the current-identity endpoint.

API-key management operates within the caller's workspace (the default one when
auth is disabled), so a deployer can mint their first key with auth off, then
switch ``BISE_AUTH_ENABLED`` on.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from bise.application.use_cases.auth.api_keys import CreateApiKey, ListApiKeys, RevokeApiKey
from bise.application.use_cases.auth.workspaces import CreateWorkspace
from bise.presentation.api.dependencies import (
    ContainerDep,
    WorkspaceDep,
    get_create_api_key,
    get_create_workspace,
    get_list_api_keys,
    get_revoke_api_key,
)
from bise.presentation.api.schemas.auth import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    CreatedApiKeyResponse,
    CreateWorkspaceRequest,
    WorkspaceResponse,
)

router = APIRouter(tags=["auth"])


@router.get("/auth/whoami", response_model=WorkspaceResponse, summary="Current workspace")
async def whoami(workspace_id: WorkspaceDep, container: ContainerDep) -> WorkspaceResponse:
    with container.unit_of_work() as uow:
        workspace = uow.workspaces.get(workspace_id)
    assert workspace is not None
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        created_at=workspace.created_at,
    )


@router.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a workspace",
)
async def create_workspace(
    body: CreateWorkspaceRequest,
    use_case: Annotated[CreateWorkspace, Depends(get_create_workspace)],
) -> WorkspaceResponse:
    return WorkspaceResponse.from_dto(use_case.execute(body.name))


@router.post(
    "/api-keys",
    response_model=CreatedApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an API key for the current workspace",
)
async def create_api_key(
    body: CreateApiKeyRequest,
    workspace_id: WorkspaceDep,
    use_case: Annotated[CreateApiKey, Depends(get_create_api_key)],
) -> CreatedApiKeyResponse:
    return CreatedApiKeyResponse.from_dto(use_case.execute(workspace_id, body.name))


@router.get("/api-keys", response_model=list[ApiKeyResponse], summary="List API keys")
async def list_api_keys(
    workspace_id: WorkspaceDep,
    use_case: Annotated[ListApiKeys, Depends(get_list_api_keys)],
) -> list[ApiKeyResponse]:
    return [ApiKeyResponse.from_dto(k) for k in use_case.execute(workspace_id)]


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
)
async def revoke_api_key(
    key_id: int,
    workspace_id: WorkspaceDep,
    use_case: Annotated[RevokeApiKey, Depends(get_revoke_api_key)],
) -> None:
    use_case.execute(workspace_id, key_id)
