"""Unit tests for the rule-based technology detector (pure, offline)."""

from __future__ import annotations

from bise.application.ports.technology_detector import PageContent
from bise.infrastructure.analyzers.tech_fingerprint import RuleBasedTechnologyDetector

WP_HTML = """
<html><head>
  <meta name="generator" content="WordPress 6.4.2" />
  <link rel="stylesheet" href="https://acme.com/wp-content/themes/x/style.css">
  <script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABCDE"></script>
  <script src="https://www.googletagmanager.com/gtag/js?id=G-ABC123XYZ"></script>
  <script>!function(f){f.fbq=...}(window);fbq('init', '123');</script>
  <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
</head><body>woocommerce-cart</body></html>
"""


def _detect(pages: list[PageContent]) -> dict[str, float]:
    detector = RuleBasedTechnologyDetector()
    return {d.name: d.confidence for d in detector.detect(pages)}


def test_detects_wordpress_with_version() -> None:
    detector = RuleBasedTechnologyDetector()
    result = {
        d.name: d for d in detector.detect([PageContent(url="https://acme.com/", html=WP_HTML)])
    }
    assert "WordPress" in result
    assert result["WordPress"].version == "6.4.2"


def test_detects_marketing_and_analytics_stack() -> None:
    names = _detect([PageContent(url="https://acme.com/", html=WP_HTML)])
    assert "Google Tag Manager" in names
    assert "Google Analytics 4" in names
    assert "Meta Pixel" in names
    assert "WooCommerce" in names


def test_detects_cloudflare_from_header() -> None:
    names = _detect(
        [PageContent(url="https://acme.com/", html="<html></html>", headers={"cf-ray": "abc-123"})]
    )
    assert "Cloudflare" in names


def test_returns_empty_for_plain_page() -> None:
    names = _detect([PageContent(url="https://acme.com/", html="<html><body>hi</body></html>")])
    assert names == {}


def test_shopify_detection() -> None:
    html = '<script src="https://cdn.shopify.com/s/files/x.js"></script>'
    names = _detect([PageContent(url="https://shop.com/", html=html)])
    assert "Shopify" in names
