"""Analyzers must degrade gracefully on malformed/empty HTML (never crash)."""

from __future__ import annotations

import pytest

from bise.application.ports.page_content import PageContent
from bise.infrastructure.analyzers.seo_analyzer import BeautifulSoupSeoAnalyzer
from bise.infrastructure.analyzers.tech_fingerprint import RuleBasedTechnologyDetector
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser

MALFORMED = [
    "",
    "<html><head><title>unclosed",
    "<<>><div class=</div><a href=>>",
    "not html at all &&& \x00 binary-ish",
    "<html>" * 500,
]


@pytest.mark.parametrize("html", MALFORMED)
def test_seo_analyzer_never_crashes(html: str) -> None:
    signals = BeautifulSoupSeoAnalyzer().analyze(PageContent(url="https://x.com/", html=html))
    assert signals.url == "https://x.com/"
    assert signals.images_total >= 0


@pytest.mark.parametrize("html", MALFORMED)
def test_tech_detector_never_crashes(html: str) -> None:
    detections = RuleBasedTechnologyDetector().detect(
        [PageContent(url="https://x.com/", html=html)]
    )
    assert isinstance(detections, list)


@pytest.mark.parametrize("html", MALFORMED)
def test_html_parser_never_crashes(html: str) -> None:
    parser = BeautifulSoupHtmlParser()
    assert isinstance(parser.extract_links(html, "https://x.com/"), list)
    # extract_title returns None or a string, never raises.
    parser.extract_title(html)
