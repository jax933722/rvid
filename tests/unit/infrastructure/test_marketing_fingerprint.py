"""Unit tests for the rule-based marketing detector (pure, offline)."""

from __future__ import annotations

from bise.application.ports.page_content import PageContent
from bise.infrastructure.analyzers.marketing_fingerprint import RuleBasedMarketingDetector

HTML = """
<html><head>
  <script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABCDE"></script>
  <script src="https://www.googletagmanager.com/gtag/js?id=AW-123456789"></script>
  <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
  <script src="https://cdn.cookielaw.org/otSDKStub.js"></script>
</head><body>
  <a href="https://wa.me/61400000000">WhatsApp us</a>
  <a href="https://calendly.com/acme/consult">Book</a>
  <form><input type="email" name="email" placeholder="Subscribe"></form>
</body></html>
"""


def _detect(html: str) -> dict[str, str]:
    detector = RuleBasedMarketingDetector()
    return {
        d.tool_name: d.category for d in detector.detect([PageContent(url="https://x/", html=html)])
    }


def test_detects_ads_pixels_and_tag_manager() -> None:
    found = _detect(HTML)
    assert found["Google Ads"] == "Advertising"
    assert found["Google Tag Manager"] == "Tag Manager"
    assert found["Meta Pixel"] == "Marketing Pixel"


def test_detects_consent_messaging_booking_and_forms() -> None:
    found = _detect(HTML)
    assert found["OneTrust"] == "Cookie / Consent"
    assert found["WhatsApp"] == "Messaging"
    assert found["Calendly"] == "Appointment Booking"
    assert found["Newsletter / Lead Form"] == "Lead / Newsletter Form"


def test_plain_page_detects_nothing() -> None:
    assert _detect("<html><body>hello</body></html>") == {}
