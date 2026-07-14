"""``EnrichmentJob`` entity — a queued unit of company enrichment work.

A job moves ``PENDING -> RUNNING -> COMPLETED | FAILED``. Illegal transitions
raise, so a background worker draining the queue can never record an impossible
state. This is the DB-backed queue that lets a whole discovered/list set enrich
without blocking the request that scheduled it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from bise.domain.errors import InvariantViolationError


class EnrichmentJobStatus(StrEnum):
    """Lifecycle of an enrichment job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class EnrichmentJob:
    """A queued request to fully enrich one company."""

    company_id: int
    status: EnrichmentJobStatus = EnrichmentJobStatus.PENDING
    attempts: int = 0
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    @property
    def is_active(self) -> bool:
        """Whether the job still occupies the queue (not yet finished)."""
        return self.status in (EnrichmentJobStatus.PENDING, EnrichmentJobStatus.RUNNING)

    def start(self) -> None:
        """Transition PENDING -> RUNNING and record the attempt."""
        if self.status is not EnrichmentJobStatus.PENDING:
            raise InvariantViolationError(f"Cannot start a job in state {self.status}")
        self.status = EnrichmentJobStatus.RUNNING
        self.attempts += 1
        self.started_at = _utcnow()
        self._touch()

    def complete(self) -> None:
        """Transition RUNNING -> COMPLETED."""
        if self.status is not EnrichmentJobStatus.RUNNING:
            raise InvariantViolationError(f"Cannot complete a job in state {self.status}")
        self.status = EnrichmentJobStatus.COMPLETED
        self.finished_at = _utcnow()
        self._touch()

    def fail(self, error: str) -> None:
        """Transition RUNNING -> FAILED, recording the reason."""
        if self.status is not EnrichmentJobStatus.RUNNING:
            raise InvariantViolationError(f"Cannot fail a job in state {self.status}")
        self.status = EnrichmentJobStatus.FAILED
        self.error = error
        self.finished_at = _utcnow()
        self._touch()

    def _touch(self) -> None:
        self.updated_at = _utcnow()
