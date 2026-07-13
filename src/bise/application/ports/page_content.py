"""Shared input type for content analyzers (technology, SEO, marketing…).

A neutral representation of a crawled page's raw material, decoupled from any
specific analyzer so multiple enrichment modules can consume it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PageContent:
    """The raw material an analyzer inspects for one page."""

    url: str
    html: str = ""
    headers: dict[str, str] = field(default_factory=dict)
