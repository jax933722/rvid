"""Use cases for API keys: create (returns raw once), list, revoke."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.auth.keygen import generate_api_key
from bise.application.dto.auth_dto import ApiKeyDTO, CreatedApiKeyDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import api_key_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.api_key import ApiKey

logger = get_logger(__name__)


class CreateApiKey:
    """Mint a new API key for a workspace, returning the raw secret exactly once."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int, name: str) -> CreatedApiKeyDTO:
        generated = generate_api_key()
        with self._uow as uow:
            if uow.workspaces.get(workspace_id) is None:
                raise NotFoundError(f"Workspace not found: {workspace_id}")
            saved = uow.api_keys.add(
                ApiKey(
                    workspace_id=workspace_id,
                    name=name,
                    key_hash=generated.key_hash,
                    prefix=generated.prefix,
                )
            )
            uow.commit()
        logger.info("api_key.created", workspace_id=workspace_id, key_id=saved.id)
        return CreatedApiKeyDTO(api_key=api_key_to_dto(saved), secret=generated.raw)


class ListApiKeys:
    """Return a workspace's API keys (metadata only, never the secret)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int) -> list[ApiKeyDTO]:
        with self._uow as uow:
            keys = uow.api_keys.list_for_workspace(workspace_id)
        return [api_key_to_dto(k) for k in keys]


class RevokeApiKey:
    """Revoke one of a workspace's API keys."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int, key_id: int) -> None:
        with self._uow as uow:
            revoked = uow.api_keys.revoke(workspace_id, key_id)
            if not revoked:
                raise NotFoundError(f"API key not found: {key_id}")
            uow.commit()
        logger.info("api_key.revoked", workspace_id=workspace_id, key_id=key_id)
