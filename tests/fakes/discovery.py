"""In-memory fake of :class:`DiscoverySourcePort` for deterministic tests."""

from __future__ import annotations

from collections.abc import Sequence

from bise.application.ports.discovery import DiscoveredBusiness, DiscoveryCriteria


class FakeDiscoverySource:
    """Returns a preconfigured list of businesses; records the last criteria."""

    def __init__(self, businesses: Sequence[DiscoveredBusiness]) -> None:
        self._businesses = list(businesses)
        self.last_criteria: DiscoveryCriteria | None = None

    def discover(self, criteria: DiscoveryCriteria) -> Sequence[DiscoveredBusiness]:
        self.last_criteria = criteria
        return self._businesses[: criteria.limit]


class KeyedFakeDiscoverySource:
    """Returns businesses keyed by ``(category, location)``.

    Lets tests verify that a campaign's rotation cursor actually sweeps
    different grid cells: each cell can yield its own distinct businesses.
    """

    def __init__(self, by_key: dict[tuple[str, str], Sequence[DiscoveredBusiness]]) -> None:
        self._by_key = {k: list(v) for k, v in by_key.items()}
        self.calls: list[tuple[str, str]] = []

    def discover(self, criteria: DiscoveryCriteria) -> Sequence[DiscoveredBusiness]:
        self.calls.append((criteria.category, criteria.location))
        businesses = self._by_key.get((criteria.category, criteria.location), [])
        return list(businesses)[: criteria.limit]
