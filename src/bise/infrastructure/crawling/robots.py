"""robots.txt compliance.

``RobotsPolicy`` decides whether a URL may be fetched and what crawl delay to
honor. It is decoupled from HTTP: a ``robots_txt_loader`` callable fetches the
raw robots.txt, so the policy is unit-testable with a fake loader (no network).
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

RobotsLoader = Callable[[str], str | None]


class RobotsPolicy:
    """Caches and evaluates robots.txt rules per host."""

    def __init__(self, user_agent: str, robots_txt_loader: RobotsLoader) -> None:
        self._user_agent = user_agent
        self._load = robots_txt_loader
        self._cache: dict[str, RobotFileParser | None] = {}

    def _parser_for(self, url: str) -> RobotFileParser | None:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._cache:
            raw = self._load(f"{origin}/robots.txt")
            if raw is None:
                # No robots.txt (or unreachable) -> permissive by convention.
                self._cache[origin] = None
            else:
                parser = RobotFileParser()
                parser.parse(raw.splitlines())
                self._cache[origin] = parser
        return self._cache[origin]

    def can_fetch(self, url: str) -> bool:
        """Return True if robots.txt allows the configured agent to fetch ``url``."""
        parser = self._parser_for(url)
        if parser is None:
            return True
        return parser.can_fetch(self._user_agent, url)

    def crawl_delay(self, url: str) -> float | None:
        """Return the crawl-delay (seconds) declared for this host, if any."""
        parser = self._parser_for(url)
        if parser is None:
            return None
        delay = parser.crawl_delay(self._user_agent)
        return float(delay) if delay is not None else None
