"""Unit tests for the BeautifulSoup SEO analyzer (pure, offline)."""

from __future__ import annotations

from bise.application.ports.page_content import PageContent
from bise.infrastructure.analyzers.seo_analyzer import BeautifulSoupSeoAnalyzer

RICH_HTML = """
<html><head>
  <title>Acme Dental — Sydney</title>
  <meta name="description" content="Gentle family dentistry in Sydney.">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="https://acme.com/">
  <meta property="og:title" content="Acme Dental">
  <meta name="twitter:card" content="summary">
  <script type="application/ld+json">{"@type":"Dentist"}</script>
</head><body>
  <h1>Welcome</h1><h2>Services</h2><h2>Contact</h2>
  <img src="a.png" alt="team">
  <img src="b.png">
  <a href="/about">About</a>
  <a href="https://acme.com/contact">Contact</a>
  <a href="https://external.example/x">External</a>
</body></html>
"""


def test_extracts_core_signals() -> None:
    s = BeautifulSoupSeoAnalyzer().analyze(PageContent(url="https://acme.com/", html=RICH_HTML))
    assert s.title == "Acme Dental — Sydney"
    assert s.meta_description == "Gentle family dentistry in Sydney."
    assert s.canonical == "https://acme.com/"
    assert s.h1_count == 1
    assert s.h2_count == 2
    assert s.has_open_graph is True
    assert s.has_twitter_card is True
    assert s.has_structured_data is True
    assert s.is_indexable is True


def test_counts_images_and_alt() -> None:
    s = BeautifulSoupSeoAnalyzer().analyze(PageContent(url="https://acme.com/", html=RICH_HTML))
    assert s.images_total == 2
    assert s.images_missing_alt == 1
    assert s.alt_coverage == 0.5


def test_counts_internal_and_external_links() -> None:
    s = BeautifulSoupSeoAnalyzer().analyze(PageContent(url="https://acme.com/", html=RICH_HTML))
    assert s.internal_links == 2  # /about and acme.com/contact
    assert s.external_links == 1  # external.example


def test_ssl_from_scheme() -> None:
    assert (
        BeautifulSoupSeoAnalyzer()
        .analyze(PageContent(url="http://acme.com/", html="<html></html>"))
        .has_ssl
        is False
    )


def test_noindex_detected() -> None:
    html = '<html><head><meta name="robots" content="noindex"></head></html>'
    assert (
        BeautifulSoupSeoAnalyzer()
        .analyze(PageContent(url="https://acme.com/", html=html))
        .is_indexable
        is False
    )
