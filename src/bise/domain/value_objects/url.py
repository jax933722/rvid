"""``Url`` value object — a validated, normalized web address."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from bise.domain.errors import InvalidValueError

_ALLOWED_SCHEMES = ("http", "https")


@dataclass(frozen=True, slots=True)
class Url:
    """An immutable, normalized HTTP(S) URL.

    Normalization lowercases the scheme and host and strips a trailing slash on
    the path so that equivalent URLs compare equal.
    """

    value: str

    def __post_init__(self) -> None:
        parsed = urlparse(self.value.strip())
        if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
            raise InvalidValueError(f"URL scheme must be http/https: {self.value!r}")
        if not parsed.netloc:
            raise InvalidValueError(f"URL must include a host: {self.value!r}")

        normalized = urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
        object.__setattr__(self, "value", normalized)

    @property
    def hostname(self) -> str:
        """The lowercased host portion, without ``www.``."""
        host = urlparse(self.value).netloc.lower()
        return host[4:] if host.startswith("www.") else host

    def __str__(self) -> str:
        return self.value
