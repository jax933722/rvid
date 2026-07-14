"""SQLAlchemy implementations of the workspace and API-key repositories."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from bise.domain.entities.api_key import ApiKey
from bise.domain.entities.workspace import Workspace
from bise.infrastructure.db.models.auth import ApiKeyModel, WorkspaceModel


def _workspace_to_entity(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        name=model.name,
        slug=model.slug,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _api_key_to_entity(model: ApiKeyModel) -> ApiKey:
    return ApiKey(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        key_hash=model.key_hash,
        prefix=model.prefix,
        revoked=model.revoked,
        last_used_at=model.last_used_at,
        created_at=model.created_at,
    )


class SqlAlchemyWorkspaceRepository:
    """Workspace persistence backed by a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, workspace: Workspace) -> Workspace:
        model = WorkspaceModel(name=workspace.name, slug=workspace.slug)
        self._session.add(model)
        self._session.flush()
        return _workspace_to_entity(model)

    def get(self, workspace_id: int) -> Workspace | None:
        model = self._session.get(WorkspaceModel, workspace_id)
        return _workspace_to_entity(model) if model is not None else None

    def get_by_slug(self, slug: str) -> Workspace | None:
        model = self._session.scalars(
            select(WorkspaceModel).where(WorkspaceModel.slug == slug)
        ).first()
        return _workspace_to_entity(model) if model is not None else None

    def list(self) -> Sequence[Workspace]:
        stmt = select(WorkspaceModel).order_by(WorkspaceModel.id.asc())
        return [_workspace_to_entity(m) for m in self._session.scalars(stmt).all()]


class SqlAlchemyApiKeyRepository:
    """API-key persistence + hash lookup backed by a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, api_key: ApiKey) -> ApiKey:
        model = ApiKeyModel(
            workspace_id=api_key.workspace_id,
            name=api_key.name,
            key_hash=api_key.key_hash,
            prefix=api_key.prefix,
            revoked=api_key.revoked,
            last_used_at=api_key.last_used_at,
        )
        self._session.add(model)
        self._session.flush()
        return _api_key_to_entity(model)

    def get_active_by_hash(self, key_hash: str) -> ApiKey | None:
        model = self._session.scalars(
            select(ApiKeyModel).where(
                ApiKeyModel.key_hash == key_hash,
                ApiKeyModel.revoked.is_(False),
            )
        ).first()
        return _api_key_to_entity(model) if model is not None else None

    def list_for_workspace(self, workspace_id: int) -> Sequence[ApiKey]:
        stmt = (
            select(ApiKeyModel)
            .where(ApiKeyModel.workspace_id == workspace_id)
            .order_by(ApiKeyModel.created_at.desc(), ApiKeyModel.id.desc())
        )
        return [_api_key_to_entity(m) for m in self._session.scalars(stmt).all()]

    def revoke(self, workspace_id: int, key_id: int) -> bool:
        model = self._session.get(ApiKeyModel, key_id)
        if model is None or model.workspace_id != workspace_id or model.revoked:
            return False
        model.revoked = True
        self._session.flush()
        return True

    def touch_last_used(self, key_id: int) -> None:
        model = self._session.get(ApiKeyModel, key_id)
        if model is not None:
            model.last_used_at = datetime.now(UTC)
            self._session.flush()
