"""DTOs for the enrichment job queue."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EnqueueEnrichmentCommand:
    """Input: enqueue enrichment for a set of companies and/or a whole list."""

    company_ids: tuple[int, ...] = ()
    list_id: int | None = None


@dataclass(frozen=True, slots=True)
class EnrichmentJobDTO:
    """Output: an enrichment job's state."""

    id: int | None
    company_id: int
    status: str
    attempts: int
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class EnqueueResultDTO:
    """Output: how many jobs an enqueue request created vs. skipped."""

    enqueued: int
    skipped: int
    jobs: tuple[EnrichmentJobDTO, ...]


@dataclass(frozen=True, slots=True)
class QueueSummaryDTO:
    """Output: queue counts by status plus the most recent jobs."""

    counts: dict[str, int]
    recent: tuple[EnrichmentJobDTO, ...]
