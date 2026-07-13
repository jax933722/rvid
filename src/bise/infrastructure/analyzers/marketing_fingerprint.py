"""Rule-based marketing detection (open rules, no paid API, no AI).

Implements :class:`MarketingDetectorPort` by matching a curated rule set against
page HTML. Detects advertising tags, tracking pixels, tag managers, chat
widgets, lead/newsletter forms, consent banners, messaging, and booking tools.

Presence-based: a tool is reported if any of its patterns matches. The rule set
is data-only so it can be externalized or extended without touching the engine.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from bise.application.ports.marketing_detector import MarketingDetection, MarketingDetectorPort
from bise.application.ports.page_content import PageContent

# --- Categories -------------------------------------------------------------
ADVERTISING = "Advertising"
PIXEL = "Marketing Pixel"
ANALYTICS = "Analytics"
TAG_MANAGER = "Tag Manager"
CHAT = "Chat / Widget"
FORMS = "Lead / Newsletter Form"
CONSENT = "Cookie / Consent"
MESSAGING = "Messaging"
BOOKING = "Appointment Booking"
POPUP = "Popup"


@dataclass(frozen=True, slots=True)
class MarketingRule:
    """A marketing tool and the HTML patterns that indicate it."""

    tool_name: str
    category: str
    patterns: tuple[str, ...]


RULES: tuple[MarketingRule, ...] = (
    MarketingRule(
        "Google Ads",
        ADVERTISING,
        (r"googleadservices\.com/pagead/conversion", r"gtag/js\?id=AW-", r"AW-\d{6,}"),
    ),
    MarketingRule("Google Analytics 4", ANALYTICS, (r"gtag/js\?id=G-[A-Z0-9]+",)),
    MarketingRule(
        "Google Tag Manager", TAG_MANAGER, (r"googletagmanager\.com/gtm\.js", r"GTM-[A-Z0-9]+")
    ),
    MarketingRule("Meta Pixel", PIXEL, (r"connect\.facebook\.net/.+/fbevents\.js", r"fbq\('init'")),
    MarketingRule(
        "LinkedIn Insight Tag",
        PIXEL,
        (r"snap\.licdn\.com/li\.lms-analytics", r"_linkedin_partner_id"),
    ),
    MarketingRule("TikTok Pixel", PIXEL, (r"analytics\.tiktok\.com",)),
    MarketingRule("Hotjar", ANALYTICS, (r"static\.hotjar\.com",)),
    MarketingRule("Microsoft Clarity", ANALYTICS, (r"clarity\.ms",)),
    MarketingRule("Intercom", CHAT, (r"widget\.intercom\.io",)),
    MarketingRule("Drift", CHAT, (r"js\.driftt\.com",)),
    MarketingRule("Tawk.to", CHAT, (r"embed\.tawk\.to",)),
    MarketingRule("Crisp", CHAT, (r"client\.crisp\.chat",)),
    MarketingRule("Mailchimp", FORMS, (r"list-manage\.com", r"chimpstatic\.com")),
    MarketingRule("HubSpot Forms", FORMS, (r"js\.hsforms\.net", r"forms\.hsforms\.com")),
    MarketingRule(
        "Newsletter / Lead Form",
        FORMS,
        (r"<input[^>]+type=[\"']email[\"']", r"name=[\"']email[\"']"),
    ),
    MarketingRule("OneTrust", CONSENT, (r"cdn\.cookielaw\.org", r"onetrust")),
    MarketingRule("Cookiebot", CONSENT, (r"consent\.cookiebot\.com",)),
    MarketingRule("Cookie Consent", CONSENT, (r"cookieconsent",)),
    MarketingRule("OptinMonster", POPUP, (r"optinmonster",)),
    MarketingRule("Privy", POPUP, (r"privy\.com",)),
    MarketingRule("WhatsApp", MESSAGING, (r"wa\.me/", r"api\.whatsapp\.com", r"whatsapp://")),
    MarketingRule("Calendly", BOOKING, (r"calendly\.com",)),
    MarketingRule("Acuity Scheduling", BOOKING, (r"acuityscheduling\.com",)),
)


class RuleBasedMarketingDetector(MarketingDetectorPort):
    """Detects marketing tools by matching a curated rule set against page HTML."""

    def __init__(self, rules: Sequence[MarketingRule] = RULES) -> None:
        self._rules = tuple(rules)

    def detect(self, pages: Sequence[PageContent]) -> list[MarketingDetection]:
        html = "\n".join(p.html for p in pages if p.html)
        detections: list[MarketingDetection] = []
        for rule in self._rules:
            evidence = self._match(rule, html)
            if evidence is not None:
                detections.append(
                    MarketingDetection(
                        tool_name=rule.tool_name, category=rule.category, evidence=evidence
                    )
                )
        return detections

    @staticmethod
    def _match(rule: MarketingRule, html: str) -> str | None:
        for pattern in rule.patterns:
            if re.search(pattern, html, re.IGNORECASE):
                return pattern
        return None
