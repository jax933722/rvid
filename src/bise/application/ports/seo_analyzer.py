"""SEO analysis port — extracts on-page SEO signals from a page.

A concrete parser lives in infrastructure; this interface keeps the SEO use
case free of any HTML-parsing dependency and swappable.
"""

from __future__ import annotations

from typing import Protocol

from bise.application.ports.page_content import PageContent
from bise.domain.value_objects.seo_signals import SeoSignals


class SeoAnalyzerPort(Protocol):
    """Extracts :class:`SeoSignals` from a page's content."""

    def analyze(self, page: PageContent) -> SeoSignals:
        """Return the on-page SEO signals for the given page."""
        ...
