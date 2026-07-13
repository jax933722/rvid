"""Unit tests for domain value objects (pure, no I/O)."""

from __future__ import annotations

import pytest

from bise.domain.errors import InvalidValueError
from bise.domain.value_objects.confidence import Confidence
from bise.domain.value_objects.seo_grade import Grade, SeoGrade
from bise.domain.value_objects.url import Url


class TestUrl:
    def test_normalizes_scheme_host_and_trailing_slash(self) -> None:
        assert Url("HTTPS://Example.com/") == Url("https://example.com")

    def test_hostname_strips_www(self) -> None:
        assert Url("https://www.acme.com/path").hostname == "acme.com"

    @pytest.mark.parametrize("bad", ["ftp://x.com", "not-a-url", "https://"])
    def test_rejects_invalid(self, bad: str) -> None:
        with pytest.raises(InvalidValueError):
            Url(bad)


class TestConfidence:
    @pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
    def test_accepts_valid_range(self, value: float) -> None:
        assert float(Confidence(value)) == value

    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_rejects_out_of_range(self, value: float) -> None:
        with pytest.raises(InvalidValueError):
            Confidence(value)


class TestSeoGrade:
    @pytest.mark.parametrize(
        ("score", "expected"),
        [(95, Grade.A), (80, Grade.B), (65, Grade.C), (45, Grade.D), (10, Grade.F)],
    )
    def test_grade_thresholds(self, score: float, expected: Grade) -> None:
        assert SeoGrade(score).grade is expected

    def test_rejects_out_of_range(self) -> None:
        with pytest.raises(InvalidValueError):
            SeoGrade(150)
