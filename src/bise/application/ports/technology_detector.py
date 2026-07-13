"""Technology detection port (a.k.a. fingerprinting).

The detector inspects page content and returns detected technologies with
confidence and evidence. A rule-based implementation lives in infrastructure; a
future ML/other detector is a drop-in replacement behind this same interface.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PageContent:
    """The raw material a detector inspects for one page."""

    url: str
    html: str = ""
    headers: dict[str, str] = field(default_factory=dict)


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
