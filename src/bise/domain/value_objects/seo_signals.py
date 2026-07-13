"""``SeoSignals`` — the raw on-page SEO signals extracted from a homepage."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeoSignals:
    """Immutable bundle of on-page SEO signals for a single page."""

    url: str
    title: str | None = None
    meta_description: str | None = None
    canonical: str | None = None
    meta_robots: str | None = None
    h1_count: int = 0
    h2_count: int = 0
    has_open_graph: bool = False
    has_twitter_card: bool = False
    has_structured_data: bool = False
    has_ssl: bool = False
    images_total: int = 0
    images_missing_alt: int = 0
    internal_links: int = 0
    external_links: int = 0
    word_count: int = 0

    @property
    def is_indexable(self) -> bool:
        """True unless a robots meta tag requests noindex."""
        return "noindex" not in (self.meta_robots or "").lower()

    @property
    def alt_coverage(self) -> float:
        """Fraction of images that have an alt attribute (1.0 when no images)."""
        if self.images_total == 0:
            return 1.0
        return (self.images_total - self.images_missing_alt) / self.images_total
