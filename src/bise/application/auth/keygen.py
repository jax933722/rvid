"""API-key generation and hashing.

Keys look like ``bise_<43 url-safe chars>``. Only the SHA-256 hash and a short
display prefix are ever stored; the raw key is returned to the caller once. Uses
the standard library only, so this stays framework-free and importable from the
application layer.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

_KEY_PREFIX = "bise_"
_PREFIX_DISPLAY_LEN = 12


@dataclass(frozen=True, slots=True)
class GeneratedKey:
    """A freshly generated key: the raw secret plus what we persist."""

    raw: str
    prefix: str
    key_hash: str


def hash_key(raw: str) -> str:
    """Return the SHA-256 hex digest used to look up a presented key."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_api_key() -> GeneratedKey:
    """Generate a new API key; the raw value is shown to the user only once."""
    raw = _KEY_PREFIX + secrets.token_urlsafe(32)
    return GeneratedKey(raw=raw, prefix=raw[:_PREFIX_DISPLAY_LEN], key_hash=hash_key(raw))
