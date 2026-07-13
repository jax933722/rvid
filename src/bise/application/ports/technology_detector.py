"""Technology detection port (a.k.a. fingerprinting).

The detector inspects page content and returns detected technologies with
confidence and evidence. A rule-based implementation lives in infrastructure; a
future ML/other detector is a drop-in replacement behind this same interface.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from bise.application.ports.page_content import PageContent

__all__ = ["PageContent", "TechDetection", "TechnologyDetectorPort"]


@dataclass(frozen=True, slots=True)
class TechDetection:
    """A single detected technology with its evidence."""

    name: str
    category: str
    confidence: float
    evidence: str
    version: str | None = None


class TechnologyDetectorPort(Protocol):
    """Detects technologies from a set of crawled pages."""

    def detect(self, pages: Sequence[PageContent]) -> list[TechDetection]:
        """Return the technologies detected across the given pages."""
        ...
