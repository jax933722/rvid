"""Response schema for the SEO API."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from pydantic import BaseModel

from bise.application.dto.seo_dto import SeoProfileDTO


class SeoProfileResponse(BaseModel):
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

    @classmethod
    def from_dto(cls, dto: SeoProfileDTO) -> SeoProfileResponse:
        return cls(**asdict(dto))
