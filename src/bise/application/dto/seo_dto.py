"""DTOs for SEO profiles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SeoProfileDTO:
    """A company's scored SEO profile."""

    url: str
    score: float
    grade: str
    title: str | None
    meta_description: str | None
    canonical: str | None
    meta_robots: str | None
    is_indexable: bool
    h1_count: int
    h2_count: int
    has_open_graph: bool
    has_twitter_card: bool
    has_structured_data: bool
    has_ssl: bool
    images_total: int
    images_missing_alt: int
    internal_links: int
    external_links: int
    word_count: int
    cwv_lcp_ms: int | None
    cwv_cls: float | None
    cwv_inp_ms: int | None
    scanned_at: datetime
