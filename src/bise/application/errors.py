"""Application-level exceptions (use-case failures).

Distinct from domain errors: these describe use-case outcomes such as
not-found or conflicting state, which the presentation layer maps to HTTP.
"""

from __future__ import annotations


class ApplicationError(Exception):
    """Base class for application/use-case failures."""


class NotFoundError(ApplicationError):
    """A requested resource does not exist."""


class ConflictError(ApplicationError):
    """The operation conflicts with existing state (e.g. duplicate domain)."""
