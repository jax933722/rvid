"""Pure page-type classification from a URL path.

Rule-based and deterministic so it is trivially unit-testable and free of any
framework or network dependency. Order matters: more specific keywords first.
"""

from __future__ import annotations

from urllib.parse import urlparse

from bise.domain.entities.crawled_page import PageType

# Ordered keyword rules: the first path substring that matches wins.
_RULES: tuple[tuple[PageType, tuple[str, ...]], ...] = (
    (PageType.CAREERS, ("career", "careers", "jobs", "join-us", "join-our-team")),
    (PageType.CONTACT, ("contact", "contact-us", "get-in-touch")),
    (PageType.ABOUT, ("about", "about-us", "who-we-are", "our-story")),
    (PageType.PRIVACY, ("privacy", "privacy-policy")),
    (PageType.TERMS, ("terms", "terms-of-service", "terms-and-conditions", "tos")),
    (PageType.BLOG, ("blog", "news", "articles", "insights")),
)


def classify_page_type(url: str, *, is_home: bool = False) -> PageType:
    """Classify a page URL into a :class:`PageType`.

    Args:
        url: The absolute or relative page URL.
        is_home: Force the HOME classification (used for the site root).
    """
    if is_home:
        return PageType.HOME

    path = urlparse(url).path.lower().strip("/")
    if not path:
        return PageType.HOME

    segments = path.split("/")
    for page_type, keywords in _RULES:
        if any(any(kw == seg or kw in seg for seg in segments) for kw in keywords):
            return page_type
    return PageType.OTHER
