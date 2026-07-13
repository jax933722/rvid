"""HTML parsing port — extracts structured data from page markup.

Keeps BeautifulSoup/lxml out of the application and crawler logic so parsing is
swappable and the orchestration stays testable with a fake parser.
"""

from __future__ import annotations

from typing import Protocol


class HtmlParserPort(Protocol):
    """Extracts links and metadata from an HTML document."""

    def extract_links(self, html: str, base_url: str) -> list[str]:
        """Return absolute URLs for all anchor hrefs, resolved against base_url."""
        ...

    def extract_title(self, html: str) -> str | None:
        """Return the document ``<title>`` text, if present."""
        ...
