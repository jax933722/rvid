"""``BeautifulSoupSeoAnalyzer`` — extracts on-page SEO signals from HTML."""

from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from bise.application.ports.page_content import PageContent
from bise.domain.value_objects.seo_signals import SeoSignals


def _host(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


class BeautifulSoupSeoAnalyzer:
    """Parses a page's HTML into :class:`SeoSignals` (bs4 + lxml)."""

    def analyze(self, page: PageContent) -> SeoSignals:
        soup = BeautifulSoup(page.html or "", "lxml")
        base_host = _host(page.url)

        internal, external = self._count_links(soup, base_host)
        images_total, images_missing_alt = self._count_images(soup)

        return SeoSignals(
            url=page.url,
            title=self._text(soup.title),
            meta_description=self._meta_content(soup, name="description"),
            canonical=self._canonical(soup),
            meta_robots=self._meta_content(soup, name="robots"),
            h1_count=len(soup.find_all("h1")),
            h2_count=len(soup.find_all("h2")),
            has_open_graph=self._has_meta_prefix(soup, "og:"),
            has_twitter_card=self._has_meta_prefix(soup, "twitter:"),
            has_structured_data=bool(soup.find("script", attrs={"type": "application/ld+json"})),
            has_ssl=page.url.lower().startswith("https://"),
            images_total=images_total,
            images_missing_alt=images_missing_alt,
            internal_links=internal,
            external_links=external,
            word_count=len(soup.get_text(" ", strip=True).split()),
        )

    # --- helpers -----------------------------------------------------------
    @staticmethod
    def _text(tag: Tag | None) -> str | None:
        if tag is None or tag.string is None:
            return None
        text = tag.string.strip()
        return text or None

    @staticmethod
    def _meta_content(soup: BeautifulSoup, *, name: str) -> str | None:
        tag = soup.find("meta", attrs={"name": name})
        if isinstance(tag, Tag):
            content = tag.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        return None

    @staticmethod
    def _canonical(soup: BeautifulSoup) -> str | None:
        tag = soup.find("link", attrs={"rel": "canonical"})
        if isinstance(tag, Tag):
            href = tag.get("href")
            if isinstance(href, str) and href.strip():
                return href.strip()
        return None

    @staticmethod
    def _has_meta_prefix(soup: BeautifulSoup, prefix: str) -> bool:
        for tag in soup.find_all("meta"):
            key = tag.get("property") or tag.get("name") or ""
            if isinstance(key, str) and key.lower().startswith(prefix):
                return True
        return False

    @staticmethod
    def _count_links(soup: BeautifulSoup, base_host: str) -> tuple[int, int]:
        internal = external = 0
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            if href.startswith(("http://", "https://")):
                if _host(href) == base_host:
                    internal += 1
                else:
                    external += 1
            elif href.startswith("/"):
                internal += 1
        return internal, external

    @staticmethod
    def _count_images(soup: BeautifulSoup) -> tuple[int, int]:
        images = soup.find_all("img")
        missing = sum(1 for img in images if not str(img.get("alt", "")).strip())
        return len(images), missing
