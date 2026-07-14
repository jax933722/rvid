"""Integration tests for the enrichment queue: enqueue, dedupe, drain, summary."""

from __future__ import annotations

from config.containers import Container

from bise.application.dto.company_dto import CreateCompanyCommand, NewDomainDTO
from bise.application.dto.enrichment_dto import EnqueueEnrichmentCommand
from bise.application.use_cases.enrichment.enqueue_enrichment import EnqueueEnrichment
from bise.application.use_cases.enrichment.get_queue_summary import GetQueueSummary
from bise.presentation.workers.enrichment_queue import process_enrichment_jobs


def _company(container: Container, name: str, host: str) -> int:
    dto = container.create_company().execute(
        CreateCompanyCommand(
            display_name=name, domains=(NewDomainDTO(hostname=host, is_primary=True),)
        )
    )
    assert dto.id is not None
    return dto.id


def test_enqueue_dedupes_active_and_unknown(container: Container) -> None:
    acme = _company(container, "Acme", "acme.com")
    enqueue = EnqueueEnrichment(container.unit_of_work())

    first = enqueue.execute(EnqueueEnrichmentCommand(company_ids=(acme,)))
    assert first.enqueued == 1 and first.skipped == 0

    # Re-enqueuing the same company is skipped (already pending).
    second = enqueue.execute(EnqueueEnrichmentCommand(company_ids=(acme, 999)))
    assert second.enqueued == 0
    assert second.skipped == 2  # acme already active + unknown company 999


def test_enqueue_for_list(container: Container) -> None:
    acme = _company(container, "Acme", "acme.com")
    beta = _company(container, "Beta", "beta.com")
    lst = container.create_company_list().execute("Targets")
    assert lst.id is not None
    container.add_company_to_list().execute(lst.id, acme)
    container.add_company_to_list().execute(lst.id, beta)

    result = EnqueueEnrichment(container.unit_of_work()).execute(
        EnqueueEnrichmentCommand(list_id=lst.id)
    )
    assert result.enqueued == 2


def test_drain_processes_jobs_with_stub_enrich(container: Container) -> None:
    acme = _company(container, "Acme", "acme.com")
    beta = _company(container, "Beta", "beta.com")
    EnqueueEnrichment(container.unit_of_work()).execute(
        EnqueueEnrichmentCommand(company_ids=(acme, beta))
    )

    seen: list[int] = []
    processed = process_enrichment_jobs(container, enrich=lambda _c, cid: seen.append(cid))
    assert processed == 2
    assert set(seen) == {acme, beta}

    summary = GetQueueSummary(container.unit_of_work()).execute()
    assert summary.counts.get("completed") == 2
    assert summary.counts.get("pending", 0) == 0


def test_drain_marks_failed_and_continues(container: Container) -> None:
    acme = _company(container, "Acme", "acme.com")
    beta = _company(container, "Beta", "beta.com")
    EnqueueEnrichment(container.unit_of_work()).execute(
        EnqueueEnrichmentCommand(company_ids=(acme, beta))
    )

    def flaky(_c: Container, company_id: int) -> None:
        if company_id == acme:
            raise RuntimeError("crawl blew up")

    processed = process_enrichment_jobs(container, enrich=flaky)
    assert processed == 2  # one failure does not stop the queue

    summary = GetQueueSummary(container.unit_of_work()).execute()
    assert summary.counts.get("failed") == 1
    assert summary.counts.get("completed") == 1
    failed = next(j for j in summary.recent if j.status == "failed")
    assert failed.error == "crawl blew up"


def test_drain_respects_max_jobs(container: Container) -> None:
    ids = [_company(container, f"C{i}", f"c{i}.com") for i in range(3)]
    EnqueueEnrichment(container.unit_of_work()).execute(
        EnqueueEnrichmentCommand(company_ids=tuple(ids))
    )
    processed = process_enrichment_jobs(container, max_jobs=2, enrich=lambda _c, _id: None)
    assert processed == 2
    summary = GetQueueSummary(container.unit_of_work()).execute()
    assert summary.counts.get("pending") == 1
