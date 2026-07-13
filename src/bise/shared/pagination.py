"""Reusable pagination primitives shared across use cases and adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 200


@dataclass(frozen=True, slots=True)
class PageRequest:
    """A request for one page of results (1-indexed)."""

    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= self.page_size <= MAX_PAGE_SIZE:
            raise ValueError(f"page_size must be within [1, {MAX_PAGE_SIZE}]")

    @property
    def offset(self) -> int:
        """Zero-based row offset for the underlying query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Maximum number of rows to fetch."""
        return self.page_size


@dataclass(frozen=True, slots=True)
class Page(Generic[T]):
    """A page of results plus the total count for the full query."""

    items: list[T]
    total: int
    page: int
    page_size: int
