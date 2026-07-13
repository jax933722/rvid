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
