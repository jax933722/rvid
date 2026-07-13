"""SQLAlchemy implementation of :class:`SeoProfileRepository`."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from bise.domain.entities.seo_profile import SeoProfile
from bise.domain.value_objects.seo_signals import SeoSignals
from bise.infrastructure.db.models.seo import SeoProfileModel


def _to_entity(model: SeoProfileModel) -> SeoProfile:
    signals = SeoSignals(
        url=model.url,
        title=model.title,
        meta_description=model.meta_description,
        canonical=model.canonical,
        meta_robots=model.meta_robots,
        h1_count=model.h1_count,
        h2_count=model.h2_count,
        has_open_graph=model.has_open_graph,
        has_twitter_card=model.has_twitter_card,
        has_structured_data=model.has_structured_data,
        has_ssl=model.has_ssl,
        images_total=model.images_total,
        images_missing_alt=model.images_missing_alt,
        internal_links=model.internal_links,
        external_links=model.external_links,
        word_count=model.word_count,
    )
    return SeoProfile(
        id=model.id,
        company_id=model.company_id,
        signals=signals,
        score=model.score,
        cwv_lcp_ms=model.cwv_lcp_ms,
        cwv_cls=model.cwv_cls,
        cwv_inp_ms=model.cwv_inp_ms,
        scanned_at=model.scanned_at,
    )


def _apply(profile: SeoProfile, model: SeoProfileModel) -> None:
    s = profile.signals
    model.url = s.url
    model.title = s.title
    model.meta_description = s.meta_description
    model.canonical = s.canonical
    model.meta_robots = s.meta_robots
    model.h1_count = s.h1_count
    model.h2_count = s.h2_count
    model.has_open_graph = s.has_open_graph
    model.has_twitter_card = s.has_twitter_card
    model.has_structured_data = s.has_structured_data
    model.has_ssl = s.has_ssl
    model.images_total = s.images_total
    model.images_missing_alt = s.images_missing_alt
    model.internal_links = s.internal_links
    model.external_links = s.external_links
    model.word_count = s.word_count
    model.score = profile.score
    model.grade = profile.grade
    model.cwv_lcp_ms = profile.cwv_lcp_ms
    model.cwv_cls = profile.cwv_cls
    model.cwv_inp_ms = profile.cwv_inp_ms
    model.scanned_at = profile.scanned_at


class SqlAlchemySeoProfileRepository:
    """One current SEO profile per company (upserted on each scan)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, profile: SeoProfile) -> SeoProfile:
        model = self._session.scalars(
            select(SeoProfileModel).where(SeoProfileModel.company_id == profile.company_id)
        ).first()
        if model is None:
            model = SeoProfileModel(company_id=profile.company_id)
            self._session.add(model)
        _apply(profile, model)
        self._session.flush()
        profile.id = model.id
        return profile

    def get_for_company(self, company_id: int) -> SeoProfile | None:
        model = self._session.scalars(
            select(SeoProfileModel).where(SeoProfileModel.company_id == company_id)
        ).first()
        return _to_entity(model) if model is not None else None
