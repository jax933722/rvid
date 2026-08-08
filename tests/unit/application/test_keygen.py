"""Unit tests for API-key generation and hashing."""

from __future__ import annotations

from bise.application.auth.keygen import generate_api_key, hash_key


def test_generated_key_has_prefix_and_matching_hash() -> None:
    key = generate_api_key()
    assert key.raw.startswith("bise_")
    assert key.prefix == key.raw[:12]
    assert key.key_hash == hash_key(key.raw)
    assert len(key.key_hash) == 64  # sha-256 hex digest


def test_keys_are_unique() -> None:
    assert generate_api_key().raw != generate_api_key().raw


def test_hash_is_stable() -> None:
    assert hash_key("bise_abc") == hash_key("bise_abc")
    assert hash_key("bise_abc") != hash_key("bise_xyz")
