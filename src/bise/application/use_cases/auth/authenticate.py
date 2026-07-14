"""Use case: resolve a presented API key to its workspace."""

from __future__ import annotations

from bise.application.auth.keygen import hash_key
from bise.application.dto.auth_dto import WorkspaceDTO
from bise.application.mappers import workspace_to_dto
from bise.application.ports.unit_of_work import UnitOfWork


class AuthenticateApiKey:
    """Look up an active API key by its hash and return its workspace, or None."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, raw_key: str) -> WorkspaceDTO | None:
        if not raw_key:
            return None
        key_hash = hash_key(raw_key)
        with self._uow as uow:
            api_key = uow.api_keys.get_active_by_hash(key_hash)
            if api_key is None:
                return None
            workspace = uow.workspaces.get(api_key.workspace_id)
            if workspace is None:
                return None
            if api_key.id is not None:
                uow.api_keys.touch_last_used(api_key.id)
                uow.commit()
            return workspace_to_dto(workspace)
