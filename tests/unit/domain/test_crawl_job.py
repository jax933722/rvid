"""Unit tests for the CrawlJob state machine."""

from __future__ import annotations

import pytest

from bise.domain.entities.crawl_job import CrawlJob, CrawlJobStatus
from bise.domain.errors import InvariantViolationError


def _job() -> CrawlJob:
    return CrawlJob(domain_id=1, hostname="acme.com")


def test_happy_path_transitions() -> None:
    job = _job()
    assert job.status is CrawlJobStatus.PENDING
    job.start()
    assert job.status is CrawlJobStatus.RUNNING
    assert job.attempts == 1
    assert job.started_at is not None
    job.complete(pages_crawled=5)
    assert job.status is CrawlJobStatus.COMPLETED
    assert job.pages_crawled == 5
    assert job.finished_at is not None


def test_cannot_start_twice() -> None:
    job = _job()
    job.start()
    with pytest.raises(InvariantViolationError):
        job.start()


def test_cannot_complete_before_start() -> None:
    with pytest.raises(InvariantViolationError):
        _job().complete(0)


def test_fail_records_error() -> None:
    job = _job()
    job.start()
    job.fail("boom")
    assert job.status is CrawlJobStatus.FAILED
    assert job.error == "boom"


def test_cannot_complete_after_fail() -> None:
    job = _job()
    job.start()
    job.fail("boom")
    with pytest.raises(InvariantViolationError):
        job.complete(1)
