"""Use cases for workspaces (tenants)."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.auth_dto import WorkspaceDTO
from bise.application.mappers import workspace_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.workspace import Workspace, slugify

logger = get_logger(__name__)


class CreateWorkspace:
    """Create a new workspace (its slug is derived from the name)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, name: str) -> WorkspaceDTO:
        with self._uow as uow:
            saved = uow.workspaces.add(Workspace(name=name))
            uow.commit()
        logger.info("workspace.created", workspace_id=saved.id, slug=saved.slug)
        return workspace_to_dto(saved)


class GetOrCreateDefaultWorkspace:
    """Idempotently ensure the default workspace exists; return it.

    Called at startup and by the auth dependency when auth is disabled, so the
    app always has a workspace to operate in without any setup.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, slug: str) -> WorkspaceDTO:
        slug = slugify(slug) or "default"
        with self._uow as uow:
            existing = uow.workspaces.get_by_slug(slug)
            if existing is not None:
                return workspace_to_dto(existing)
            saved = uow.workspaces.add(Workspace(name=slug.replace("-", " ").title(), slug=slug))
            uow.commit()
        logger.info("workspace.default_created", workspace_id=saved.id, slug=saved.slug)
        return workspace_to_dto(saved)
