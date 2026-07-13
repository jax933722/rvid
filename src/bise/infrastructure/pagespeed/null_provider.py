"""Null Core Web Vitals provider — the zero-dependency default.

Returns ``None`` so the system needs no paid or external performance API. A real
provider (self-hosted Lighthouse, an open CrUX mirror, …) can replace this
behind :class:`PageSpeedPort` without touching SEO business logic.
"""

from __future__ import annotations

from bise.application.ports.page_speed import CoreWebVitals


class NullPageSpeedProvider:
    """A :class:`PageSpeedPort` that reports no metrics."""

    def get_metrics(self, url: str) -> CoreWebVitals | None:
        return None
