"""Unit tests for the EnrichmentJob state machine."""

from __future__ import annotations

import pytest

from bise.domain.entities.enrichment_job import EnrichmentJob, EnrichmentJobStatus
from bise.domain.errors import InvariantViolationError


def test_happy_path_transitions() -> None:
    job = EnrichmentJob(company_id=1)
    assert job.is_active
    job.start()
    assert job.status is EnrichmentJobStatus.RUNNING
    assert job.attempts == 1
    assert job.started_at is not None
    job.complete()
    assert job.status is EnrichmentJobStatus.COMPLETED
    assert not job.is_active
    assert job.finished_at is not None


def test_failure_records_reason() -> None:
    job = EnrichmentJob(company_id=1)
    job.start()
    job.fail("boom")
    assert job.status is EnrichmentJobStatus.FAILED
    assert job.error == "boom"


def test_cannot_start_twice() -> None:
    job = EnrichmentJob(company_id=1)
    job.start()
    with pytest.raises(InvariantViolationError):
        job.start()


def test_cannot_complete_before_start() -> None:
    with pytest.raises(InvariantViolationError):
        EnrichmentJob(company_id=1).complete()


def test_cannot_fail_before_start() -> None:
    with pytest.raises(InvariantViolationError):
        EnrichmentJob(company_id=1).fail("x")
