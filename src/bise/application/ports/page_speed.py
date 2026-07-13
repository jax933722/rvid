"""Core Web Vitals port — a pluggable performance-metrics provider.

The default implementation (infrastructure) returns ``None`` so the system has
no paid/external dependency. A real provider (e.g. a self-hosted Lighthouse or
an open CrUX mirror) can be plugged in later behind this same interface without
changing SEO business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CoreWebVitals:
    """Core Web Vitals metrics for a URL."""

    lcp_ms: int | None = None
    cls: float | None = None
    inp_ms: int | None = None


class PageSpeedPort(Protocol):
    """Provides Core Web Vitals for a URL, or ``None`` if unavailable."""

    def get_metrics(self, url: str) -> CoreWebVitals | None:
        """Return performance metrics for the URL, or ``None`` when unsupported."""
        ...
