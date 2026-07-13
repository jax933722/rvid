"""Unit of Work port — a transaction boundary abstraction.

Use cases open a UoW, perform repository operations, then commit or roll back
atomically. The concrete implementation (SQLAlchemy) lives in infrastructure.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol

from bise.application.ports.repositories import CompanyRepository


class UnitOfWork(Protocol):
    """A transactional scope exposing the repositories it coordinates."""

    companies: CompanyRepository

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None:
        """Persist all changes made within this scope."""
        ...

    def rollback(self) -> None:
        """Discard all changes made within this scope."""
        ...
