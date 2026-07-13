"""``SeoGrade`` value object — a letter grade derived from a 0-100 SEO score."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from bise.domain.errors import InvalidValueError


class Grade(StrEnum):
    """Letter grades from A (best) to F (worst)."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass(frozen=True, slots=True)
class SeoGrade:
    """A letter grade computed deterministically from a numeric SEO score."""

    score: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 100.0:
            raise InvalidValueError(f"SEO score must be within [0, 100]: {self.score!r}")

    @property
    def grade(self) -> Grade:
        """Map the score to a letter grade using fixed thresholds."""
        if self.score >= 90:
            return Grade.A
        if self.score >= 75:
            return Grade.B
        if self.score >= 60:
            return Grade.C
        if self.score >= 40:
            return Grade.D
        return Grade.F

    def __str__(self) -> str:
        return self.grade.value
