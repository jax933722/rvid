"""``Confidence`` value object — a bounded [0, 1] certainty score.

Used across derived data (technology detection, classification, company
intelligence) to record how sure the system is about an inferred value.
"""

from __future__ import annotations

from dataclasses import dataclass

from bise.domain.errors import InvalidValueError


@dataclass(frozen=True, slots=True)
class Confidence:
    """An immutable confidence score in the inclusive range [0.0, 1.0]."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidValueError(f"Confidence must be within [0.0, 1.0]: {self.value!r}")

    @classmethod
    def certain(cls) -> Confidence:
        """A confidence of 1.0 (direct, unambiguous evidence)."""
        return cls(1.0)

    @classmethod
    def unknown(cls) -> Confidence:
        """A confidence of 0.0 (no evidence)."""
        return cls(0.0)

    def __float__(self) -> float:
        return self.value
