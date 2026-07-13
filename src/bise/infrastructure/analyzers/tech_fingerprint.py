"""Rule-based technology fingerprinting (Wappalyzer-style, open rules).

Implements :class:`TechnologyDetectorPort` with a curated, deterministic rule
set matched against page HTML and response headers. No paid API, no AI. A rule
matches when any of its patterns matches; the technology's confidence is the
highest matching pattern confidence, and an optional ``version`` named group is
captured when present.

The rule set is intentionally data-only so it can later be externalized to a
JSON file or expanded without touching the detection engine.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from bise.application.ports.technology_detector import (
    PageContent,
    TechDetection,
    TechnologyDetectorPort,
)


class Kind(Enum):
    """Where a pattern is evaluated."""

    HTML = "html"  # matched against page HTML (incl. script tags)
    HEADER = "header"  # matched against a named response header value
    META_GEN = "meta_gen"  # matched against the <meta name=generator> content


@dataclass(frozen=True, slots=True)
class Pattern:
    """One indicator for a technology."""

    kind: Kind
    regex: str
    header: str | None = None
    confidence: float = 0.8


@dataclass(frozen=True, slots=True)
class Rule:
    """A technology and the patterns that indicate it."""

    name: str
    category: str
    patterns: tuple[Pattern, ...]
    vendor: str | None = None


# --- Categories -------------------------------------------------------------
CMS = "CMS"
ECOMMERCE = "E-commerce"
FRAMEWORK = "JavaScript Framework"
BACKEND = "Web Framework"
ANALYTICS = "Analytics"
TAG_MANAGER = "Tag Manager"
PIXEL = "Marketing Pixel"
CRM = "CRM"
CDN = "CDN / Hosting"
CHAT = "Chat / Widget"

# --- Rule set ---------------------------------------------------------------
RULES: tuple[Rule, ...] = (
    Rule(
        "WordPress",
        CMS,
        (
            Pattern(Kind.HTML, r"/wp-content/", confidence=0.9),
            Pattern(Kind.HTML, r"/wp-json/", confidence=0.9),
            Pattern(Kind.META_GEN, r"WordPress(?:\s+(?P<version>[\d.]+))?", confidence=0.95),
        ),
    ),
    Rule("WooCommerce", ECOMMERCE, (Pattern(Kind.HTML, r"woocommerce", confidence=0.85),)),
    Rule(
        "Shopify",
        ECOMMERCE,
        (
            Pattern(Kind.HTML, r"cdn\.shopify\.com", confidence=0.95),
            Pattern(Kind.HTML, r"Shopify\.theme", confidence=0.9),
        ),
    ),
    Rule(
        "Magento",
        ECOMMERCE,
        (
            Pattern(Kind.HTML, r"/static/version\d+/frontend/", confidence=0.85),
            Pattern(Kind.HTML, r"Magento", confidence=0.7),
        ),
    ),
    Rule(
        "Drupal",
        CMS,
        (
            Pattern(Kind.HTML, r"/sites/(?:all|default)/", confidence=0.8),
            Pattern(Kind.META_GEN, r"Drupal(?:\s+(?P<version>[\d.]+))?", confidence=0.95),
        ),
    ),
    Rule(
        "Joomla",
        CMS,
        (
            Pattern(Kind.META_GEN, r"Joomla", confidence=0.95),
            Pattern(Kind.HTML, r"/media/jui/", confidence=0.8),
        ),
    ),
    Rule(
        "React",
        FRAMEWORK,
        (
            Pattern(Kind.HTML, r"data-reactroot", confidence=0.85),
            Pattern(Kind.HTML, r"/static/js/react", confidence=0.7),
        ),
    ),
    Rule(
        "Angular",
        FRAMEWORK,
        (
            Pattern(Kind.HTML, r"ng-version=\"(?P<version>[\d.]+)\"", confidence=0.9),
            Pattern(Kind.HTML, r"ng-app", confidence=0.6),
        ),
    ),
    Rule(
        "Vue.js",
        FRAMEWORK,
        (
            Pattern(Kind.HTML, r"data-v-[0-9a-f]{8}", confidence=0.75),
            Pattern(Kind.HTML, r"vue(?:\.min)?\.js", confidence=0.7),
        ),
    ),
    Rule(
        "Next.js",
        FRAMEWORK,
        (
            Pattern(Kind.HTML, r"/_next/static/", confidence=0.9),
            Pattern(Kind.HTML, r"__NEXT_DATA__", confidence=0.9),
        ),
    ),
    Rule(
        "Nuxt.js",
        FRAMEWORK,
        (
            Pattern(Kind.HTML, r"/_nuxt/", confidence=0.9),
            Pattern(Kind.HTML, r"__NUXT__", confidence=0.9),
        ),
    ),
    Rule(
        "Laravel",
        BACKEND,
        (
            Pattern(Kind.HEADER, r"laravel_session", header="set-cookie", confidence=0.9),
            Pattern(Kind.HTML, r"csrf-token", confidence=0.4),
        ),
    ),
    Rule(
        "HubSpot",
        CRM,
        (
            Pattern(Kind.HTML, r"js\.hs-scripts\.com", confidence=0.9),
            Pattern(Kind.HTML, r"hsubspot|hs-analytics", confidence=0.6),
        ),
    ),
    Rule(
        "Salesforce",
        CRM,
        (
            Pattern(Kind.HTML, r"salesforce\.com", confidence=0.6),
            Pattern(Kind.HTML, r"pardot", confidence=0.7),
        ),
    ),
    Rule(
        "Cloudflare",
        CDN,
        (
            Pattern(Kind.HEADER, r".+", header="cf-ray", confidence=0.95),
            Pattern(Kind.HEADER, r"cloudflare", header="server", confidence=0.9),
        ),
    ),
    Rule(
        "Google Tag Manager",
        TAG_MANAGER,
        (
            Pattern(Kind.HTML, r"googletagmanager\.com/gtm\.js", confidence=0.95),
            Pattern(Kind.HTML, r"GTM-[A-Z0-9]+", confidence=0.9),
        ),
    ),
    Rule(
        "Google Analytics",
        ANALYTICS,
        (
            Pattern(Kind.HTML, r"google-analytics\.com/analytics\.js", confidence=0.9),
            Pattern(Kind.HTML, r"UA-\d{4,}-\d+", confidence=0.9),
        ),
    ),
    Rule(
        "Google Analytics 4",
        ANALYTICS,
        (
            Pattern(Kind.HTML, r"gtag/js\?id=G-[A-Z0-9]+", confidence=0.95),
            Pattern(Kind.HTML, r"G-[A-Z0-9]{6,}", confidence=0.75),
        ),
    ),
    Rule(
        "Meta Pixel",
        PIXEL,
        (
            Pattern(Kind.HTML, r"connect\.facebook\.net/.+/fbevents\.js", confidence=0.95),
            Pattern(Kind.HTML, r"fbq\('init'", confidence=0.9),
        ),
    ),
    Rule(
        "LinkedIn Insight Tag",
        PIXEL,
        (
            Pattern(Kind.HTML, r"snap\.licdn\.com/li\.lms-analytics", confidence=0.95),
            Pattern(Kind.HTML, r"_linkedin_partner_id", confidence=0.9),
        ),
    ),
    Rule("TikTok Pixel", PIXEL, (Pattern(Kind.HTML, r"analytics\.tiktok\.com", confidence=0.95),)),
    Rule(
        "Hotjar",
        ANALYTICS,
        (
            Pattern(Kind.HTML, r"static\.hotjar\.com", confidence=0.95),
            Pattern(Kind.HTML, r"hjid", confidence=0.6),
        ),
    ),
    Rule("Microsoft Clarity", ANALYTICS, (Pattern(Kind.HTML, r"clarity\.ms", confidence=0.95),)),
    Rule("Intercom", CHAT, (Pattern(Kind.HTML, r"widget\.intercom\.io", confidence=0.95),)),
    Rule("Drift", CHAT, (Pattern(Kind.HTML, r"js\.driftt\.com", confidence=0.95),)),
    Rule("Tawk.to", CHAT, (Pattern(Kind.HTML, r"embed\.tawk\.to", confidence=0.95),)),
)

_META_GENERATOR = re.compile(
    r"<meta[^>]+name=[\"']generator[\"'][^>]+content=[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)


class RuleBasedTechnologyDetector(TechnologyDetectorPort):
    """Detects technologies by matching a curated rule set against page content."""

    def __init__(self, rules: Sequence[Rule] = RULES) -> None:
        self._rules = tuple(rules)

    def detect(self, pages: Sequence[PageContent]) -> list[TechDetection]:
        html = "\n".join(p.html for p in pages if p.html)
        headers = self._merge_headers(pages)
        generator = self._generator(html)

        detections: list[TechDetection] = []
        for rule in self._rules:
            best = self._match_rule(rule, html, headers, generator)
            if best is not None:
                detections.append(best)
        return detections

    # --- internals ---------------------------------------------------------
    @staticmethod
    def _merge_headers(pages: Sequence[PageContent]) -> dict[str, str]:
        merged: dict[str, str] = {}
        for page in pages:
            for key, value in page.headers.items():
                merged.setdefault(key.lower(), value)
        return merged

    @staticmethod
    def _generator(html: str) -> str:
        match = _META_GENERATOR.search(html)
        return match.group(1) if match else ""

    def _match_rule(
        self, rule: Rule, html: str, headers: dict[str, str], generator: str
    ) -> TechDetection | None:
        best_conf = 0.0
        evidence = ""
        version: str | None = None

        for pattern in rule.patterns:
            match = self._match_pattern(pattern, html, headers, generator)
            if match is None:
                continue
            if pattern.confidence > best_conf:
                best_conf = pattern.confidence
                evidence = f"{pattern.kind.value}:{pattern.regex}"
            if version is None and "version" in match.groupdict():
                version = match.group("version")

        if best_conf == 0.0:
            return None
        return TechDetection(
            name=rule.name,
            category=rule.category,
            confidence=best_conf,
            evidence=evidence,
            version=version,
        )

    @staticmethod
    def _match_pattern(
        pattern: Pattern, html: str, headers: dict[str, str], generator: str
    ) -> re.Match[str] | None:
        flags = re.IGNORECASE
        if pattern.kind is Kind.HTML:
            return re.search(pattern.regex, html, flags)
        if pattern.kind is Kind.META_GEN:
            return re.search(pattern.regex, generator, flags)
        if pattern.kind is Kind.HEADER and pattern.header is not None:
            value = headers.get(pattern.header.lower())
            return re.search(pattern.regex, value, flags) if value is not None else None
        return None
