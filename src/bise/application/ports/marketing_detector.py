"""Marketing detection port.

Detects marketing/advertising tooling (ad tags, pixels, tag managers, forms,
chat, consent banners, booking, messaging) from crawled pages. Rule-based today;
a different implementation is a drop-in replacement behind this interface.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from bise.application.ports.page_content import PageContent


@dataclass(frozen=True, slots=True)
class MarketingDetection:
    """A single detected marketing tool with its evidence."""

    tool_name: str
    category: str
    evidence: str


class MarketingDetectorPort(Protocol):
    """Detects marketing tools from a set of crawled pages."""

    def detect(self, pages: Sequence[PageContent]) -> list[MarketingDetection]:
        """Return the marketing tools detected across the given pages."""
        ...
