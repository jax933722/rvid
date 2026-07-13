"""Unit tests for the deterministic SEO scorer."""

from __future__ import annotations

from bise.domain.services.seo_scoring import compute_seo_score
from bise.domain.value_objects.seo_grade import Grade, SeoGrade
from bise.domain.value_objects.seo_signals import SeoSignals


def _full_signals() -> SeoSignals:
    return SeoSignals(
        url="https://acme.com/",
        title="Acme Dental — Sydney Dentist",
        meta_description="Acme Dental provides gentle family dentistry in Sydney with modern care.",
        canonical="https://acme.com/",
        meta_robots="index,follow",
        h1_count=1,
        h2_count=3,
        has_open_graph=True,
        has_twitter_card=True,
        has_structured_data=True,
        has_ssl=True,
        images_total=4,
        images_missing_alt=0,
        internal_links=10,
        external_links=2,
        word_count=800,
    )


def test_full_signals_score_is_high() -> None:
    score = compute_seo_score(_full_signals())
    assert score >= 95
    assert SeoGrade(score).grade is Grade.A


def test_empty_page_scores_low() -> None:
    signals = SeoSignals(url="https://acme.com/", has_ssl=False)
    score = compute_seo_score(signals)
    # No title/description/h1/canonical/og/ssl; only alt-coverage (no images) counts.
    assert score < 40
    assert SeoGrade(score).grade is Grade.F


def test_noindex_costs_points() -> None:
    base = _full_signals()
    indexed_score = compute_seo_score(base)
    noindex_signals = SeoSignals(
        url=base.url,
        title=base.title,
        meta_description=base.meta_description,
        canonical=base.canonical,
        meta_robots="noindex",
        h1_count=1,
        has_open_graph=True,
        has_structured_data=True,
        has_ssl=True,
        images_total=4,
        images_missing_alt=0,
        internal_links=10,
    )
    assert compute_seo_score(noindex_signals) < indexed_score


def test_missing_alt_reduces_score() -> None:
    good = _full_signals()
    bad = SeoSignals(
        url=good.url,
        title=good.title,
        meta_description=good.meta_description,
        canonical=good.canonical,
        meta_robots="index",
        h1_count=1,
        has_open_graph=True,
        has_structured_data=True,
        has_ssl=True,
        images_total=4,
        images_missing_alt=4,
        internal_links=10,
    )
    assert compute_seo_score(bad) < compute_seo_score(good)
