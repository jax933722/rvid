"""SQLAlchemy implementation of :class:`EnrichmentJobRepository`."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bise.domain.entities.enrichment_job import EnrichmentJob, EnrichmentJobStatus
from bise.infrastructure.db.models.enrichment import EnrichmentJobModel
from bise.shared.pagination import Page, PageRequest

_ACTIVE = (EnrichmentJobStatus.PENDING.value, EnrichmentJobStatus.RUNNING.value)


def _to_entity(model: EnrichmentJobModel) -> EnrichmentJob:
    return EnrichmentJob(
        id=model.id,
        company_id=model.company_id,
        status=EnrichmentJobStatus(model.status),
        attempts=model.attempts,
        error=model.error,
        started_at=model.started_at,
        finished_at=model.finished_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyEnrichmentJobRepository:
    """Enrichment job persistence + queue picking backed by a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, job: EnrichmentJob) -> EnrichmentJob:
        model = EnrichmentJobModel(
            company_id=job.company_id,
            status=job.status.value,
            attempts=job.attempts,
            error=job.error,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def get(self, job_id: int) -> EnrichmentJob | None:
        model = self._session.get(EnrichmentJobModel, job_id)
        return _to_entity(model) if model is not None else None

    def update(self, job: EnrichmentJob) -> None:
        assert job.id is not None, "Cannot update an unsaved enrichment job"
        model = self._session.get(EnrichmentJobModel, job.id)
        if model is None:
            raise KeyError(f"EnrichmentJob not found: {job.id}")
        model.status = job.status.value
        model.attempts = job.attempts
        model.error = job.error
        model.started_at = job.started_at
        model.finished_at = job.finished_at
        self._session.flush()

    def next_pending(self) -> EnrichmentJob | None:
        stmt = (
            select(EnrichmentJobModel)
            .where(EnrichmentJobModel.status == EnrichmentJobStatus.PENDING.value)
            .order_by(EnrichmentJobModel.created_at.asc(), EnrichmentJobModel.id.asc())
            .limit(1)
        )
        model = self._session.scalars(stmt).first()
        return _to_entity(model) if model is not None else None

    def has_active_for_company(self, company_id: int) -> bool:
        stmt = select(EnrichmentJobModel.id).where(
            EnrichmentJobModel.company_id == company_id,
            EnrichmentJobModel.status.in_(_ACTIVE),
        )
        return self._session.scalars(stmt).first() is not None

    def list(
        self, page: PageRequest, status: EnrichmentJobStatus | None = None
    ) -> Page[EnrichmentJob]:
        base = select(EnrichmentJobModel)
        count_stmt = select(func.count()).select_from(EnrichmentJobModel)
        if status is not None:
            base = base.where(EnrichmentJobModel.status == status.value)
            count_stmt = count_stmt.where(EnrichmentJobModel.status == status.value)

        total = self._session.scalar(count_stmt) or 0
        stmt = (
            base.order_by(EnrichmentJobModel.created_at.desc(), EnrichmentJobModel.id.desc())
            .offset(page.offset)
            .limit(page.limit)
        )
        models = self._session.scalars(stmt).all()
        return Page(
            items=[_to_entity(m) for m in models],
            total=total,
            page=page.page,
            page_size=page.page_size,
        )

    def counts_by_status(self) -> dict[str, int]:
        rows = self._session.execute(
            select(EnrichmentJobModel.status, func.count()).group_by(EnrichmentJobModel.status)
        ).all()
        return {status: count for status, count in rows}
