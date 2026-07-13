"""SQLAlchemy implementation of :class:`MarketingSignalRepository`."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from bise.domain.entities.marketing_signal import MarketingSignal
from bise.infrastructure.db.models.marketing import MarketingSignalModel


class SqlAlchemyMarketingSignalRepository:
    """Company marketing detections (tall table; replaced on each detection)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def replace_for_company(self, company_id: int, signals: list[MarketingSignal]) -> None:
        self._session.execute(
            delete(MarketingSignalModel).where(MarketingSignalModel.company_id == company_id)
        )
        for signal in signals:
            self._session.add(
                MarketingSignalModel(
                    company_id=company_id,
                    tool_name=signal.tool_name,
                    category=signal.category,
                    evidence=signal.evidence,
                    detected_at=signal.detected_at,
                )
            )
        self._session.flush()

    def list_for_company(self, company_id: int) -> list[MarketingSignal]:
        stmt = (
            select(MarketingSignalModel)
            .where(MarketingSignalModel.company_id == company_id)
            .order_by(MarketingSignalModel.id)
        )
        return [
            MarketingSignal(
                id=m.id,
                company_id=m.company_id,
                tool_name=m.tool_name,
                category=m.category,
                evidence=m.evidence or "",
                detected_at=m.detected_at,
            )
            for m in self._session.scalars(stmt).all()
        ]
