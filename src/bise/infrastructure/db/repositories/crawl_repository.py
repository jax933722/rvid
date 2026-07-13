"""SQLAlchemy implementations of the crawl repositories."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bise.domain.entities.crawl_job import CrawlJob, CrawlJobStatus, CrawlJobType
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.infrastructure.db.models.crawl import CrawledPageModel, CrawlJobModel
from bise.shared.pagination import Page, PageRequest


def _job_to_entity(model: CrawlJobModel) -> CrawlJob:
    return CrawlJob(
        id=model.id,
        domain_id=model.domain_id,
        hostname=model.hostname,
        job_type=CrawlJobType(model.job_type),
        status=CrawlJobStatus(model.status),
        attempts=model.attempts,
        pages_crawled=model.pages_crawled,
        error=model.error,
        started_at=model.started_at,
        finished_at=model.finished_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _apply_job(entity: CrawlJob, model: CrawlJobModel) -> None:
    model.status = entity.status.value
    model.attempts = entity.attempts
    model.pages_crawled = entity.pages_crawled
    model.error = entity.error
    model.started_at = entity.started_at
    model.finished_at = entity.finished_at


class SqlAlchemyCrawlJobRepository:
    """Crawl job persistence backed by a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, job: CrawlJob) -> CrawlJob:
        model = CrawlJobModel(
            domain_id=job.domain_id,
            hostname=job.hostname,
            job_type=job.job_type.value,
            status=job.status.value,
            attempts=job.attempts,
            pages_crawled=job.pages_crawled,
            error=job.error,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )
        self._session.add(model)
        self._session.flush()
        return _job_to_entity(model)

    def get(self, job_id: int) -> CrawlJob | None:
        model = self._session.get(CrawlJobModel, job_id)
        return _job_to_entity(model) if model is not None else None

    def update(self, job: CrawlJob) -> None:
        assert job.id is not None, "Cannot update an unsaved crawl job"
        model = self._session.get(CrawlJobModel, job.id)
        if model is None:
            raise KeyError(f"CrawlJob not found: {job.id}")
        _apply_job(job, model)
        self._session.flush()

    def list(self, page: PageRequest, status: CrawlJobStatus | None = None) -> Page[CrawlJob]:
        base = select(CrawlJobModel)
        count_stmt = select(func.count()).select_from(CrawlJobModel)
        if status is not None:
            base = base.where(CrawlJobModel.status == status.value)
            count_stmt = count_stmt.where(CrawlJobModel.status == status.value)

        total = self._session.scalar(count_stmt) or 0
        stmt = (
            base.order_by(CrawlJobModel.created_at.desc(), CrawlJobModel.id.desc())
            .offset(page.offset)
            .limit(page.limit)
        )
        models = self._session.scalars(stmt).all()
        return Page(
            items=[_job_to_entity(m) for m in models],
            total=total,
            page=page.page,
            page_size=page.page_size,
        )


class SqlAlchemyCrawledPageRepository:
    """Crawled page persistence backed by a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, page: CrawledPage) -> CrawledPage:
        model = CrawledPageModel(
            crawl_job_id=page.crawl_job_id,
            domain_id=page.domain_id,
            url=page.url,
            page_type=page.page_type.value,
            http_status=page.http_status,
            content_type=page.content_type,
            title=page.title,
            content_hash=page.content_hash,
            fetched_at=page.fetched_at,
        )
        self._session.add(model)
        self._session.flush()
        page.id = model.id
        return page

    def list_for_job(self, crawl_job_id: int) -> list[CrawledPage]:
        stmt = (
            select(CrawledPageModel)
            .where(CrawledPageModel.crawl_job_id == crawl_job_id)
            .order_by(CrawledPageModel.id)
        )
        return [
            CrawledPage(
                id=m.id,
                crawl_job_id=m.crawl_job_id,
                domain_id=m.domain_id,
                url=m.url,
                page_type=PageType(m.page_type),
                http_status=m.http_status,
                content_type=m.content_type,
                title=m.title,
                content_hash=m.content_hash,
                fetched_at=m.fetched_at,
            )
            for m in self._session.scalars(stmt).all()
        ]
