"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from bise.presentation.api.dependencies import ContainerDep

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return a static OK — confirms the process is up."""
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness probe")
async def ready(container: ContainerDep) -> dict[str, str]:
    """Confirm dependencies (the database) are reachable."""
    with container.engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready"}
