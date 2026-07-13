"""Smoke tests confirming the package scaffold is importable and healthy."""

import bise


def test_package_imports() -> None:
    assert bise.__version__ == "0.1.0"
