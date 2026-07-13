"""Domain-level exceptions.

Raised when a business invariant is violated. These are pure and framework-free;
the presentation layer maps them to transport concerns (e.g. HTTP 4xx).
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain rule violations."""


class InvalidValueError(DomainError):
    """A value object was constructed from invalid input."""


class InvariantViolationError(DomainError):
    """An entity/aggregate invariant was violated."""
