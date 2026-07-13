"""``BeautifulSoupHtmlParser`` — an :class:`HtmlParserPort` using bs4 + lxml."""

from __future__ import annotations

from urllib.parse import urldefrag, urljoin

from bs4 import BeautifulSoup


class BeautifulSoupHtmlParser:
    """Extracts links and titles from HTML using BeautifulSoup with the lxml parser."""

    def _soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def extract_links(self, html: str, base_url: str) -> list[str]:
        soup = self._soup(html)
        seen: set[str] = set()
        links: list[str] = []
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            absolute, _ = urldefrag(urljoin(base_url, href))
            if absolute.startswith(("http://", "https://")) and absolute not in seen:
                seen.add(absolute)
                links.append(absolute)
        return links

    def extract_title(self, html: str) -> str | None:
        soup = self._soup(html)
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return None
