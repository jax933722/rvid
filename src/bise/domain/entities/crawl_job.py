"""``CrawlJob`` entity — a unit of crawl work with an explicit state machine.

A job moves ``PENDING -> RUNNING -> COMPLETED | FAILED``. Illegal transitions
raise, so the pipeline can never report an impossible state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from bise.domain.errors import InvariantViolationError


class CrawlJobStatus(StrEnum):
    """Lifecycle of a crawl job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlJobType(StrEnum):
    """The kind of crawl work a job represents."""

    WEBSITE = "website"


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class CrawlJob:
    """A crawl job targeting one domain."""

    domain_id: int
    hostname: str
    job_type: CrawlJobType = CrawlJobType.WEBSITE
    status: CrawlJobStatus = CrawlJobStatus.PENDING
    attempts: int = 0
    pages_crawled: int = 0
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def start(self) -> None:
        """Transition PENDING -> RUNNING and record the attempt."""
        if self.status is not CrawlJobStatus.PENDING:
            raise InvariantViolationError(f"Cannot start a job in state {self.status}")
        self.status = CrawlJobStatus.RUNNING
        self.attempts += 1
        self.started_at = _utcnow()
        self._touch()

    def complete(self, pages_crawled: int) -> None:
        """Transition RUNNING -> COMPLETED with the number of pages fetched."""
        if self.status is not CrawlJobStatus.RUNNING:
            raise InvariantViolationError(f"Cannot complete a job in state {self.status}")
        if pages_crawled < 0:
            raise InvariantViolationError("pages_crawled must be non-negative")
        self.status = CrawlJobStatus.COMPLETED
        self.pages_crawled = pages_crawled
        self.finished_at = _utcnow()
        self._touch()

    def fail(self, error: str) -> None:
        """Transition RUNNING -> FAILED, recording the reason."""
        if self.status is not CrawlJobStatus.RUNNING:
            raise InvariantViolationError(f"Cannot fail a job in state {self.status}")
        self.status = CrawlJobStatus.FAILED
        self.error = error
        self.finished_at = _utcnow()
        self._touch()

    def _touch(self) -> None:
        self.updated_at = _utcnow()
