"""Deterministic SEO scoring (pure domain logic).

Turns :class:`SeoSignals` into a 0-100 score using a transparent, weighted
checklist. Deterministic and framework-free, so it is trivially unit-testable
and the weights can evolve safely.
"""

from __future__ import annotations

from bise.domain.value_objects.seo_signals import SeoSignals

# (points, predicate) — weights sum to 100.
_TITLE = 18
_META_DESC = 15
_SINGLE_H1 = 12
_CANONICAL = 10
_INDEXABLE = 10
_OPEN_GRAPH = 8
_STRUCTURED_DATA = 8
_SSL = 9
_ALT = 6
_INTERNAL_LINKS = 4


def compute_seo_score(signals: SeoSignals) -> float:
    """Compute a 0-100 SEO score from on-page signals."""
    score = 0.0

    if signals.title and 10 <= len(signals.title) <= 60:
        score += _TITLE
    elif signals.title:
        score += _TITLE / 2

    if signals.meta_description and 50 <= len(signals.meta_description) <= 160:
        score += _META_DESC
    elif signals.meta_description:
        score += _META_DESC / 2

    if signals.h1_count == 1:
        score += _SINGLE_H1
    elif signals.h1_count > 1:
        score += _SINGLE_H1 / 2

    if signals.canonical:
        score += _CANONICAL
    if signals.is_indexable:
        score += _INDEXABLE
    if signals.has_open_graph:
        score += _OPEN_GRAPH
    if signals.has_structured_data:
        score += _STRUCTURED_DATA
    if signals.has_ssl:
        score += _SSL

    score += _ALT * signals.alt_coverage
    if signals.internal_links > 0:
        score += _INTERNAL_LINKS

    return round(min(score, 100.0), 2)
