"""Unit tests for the LeadCampaign rotation + due logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from bise.domain.entities.lead_campaign import LeadCampaign
from bise.domain.errors import InvalidValueError


def _campaign(**kw: object) -> LeadCampaign:
    base: dict[str, object] = {
        "name": "Dentists AU",
        "categories": ["dentist", "orthodontist"],
        "locations": ["Sydney", "Melbourne"],
    }
    base.update(kw)
    return LeadCampaign(**base)  # type: ignore[arg-type]


def test_requires_categories_and_locations() -> None:
    with pytest.raises(InvalidValueError):
        LeadCampaign(name="x", categories=[], locations=["Sydney"])
    with pytest.raises(InvalidValueError):
        LeadCampaign(name="x", categories=["dentist"], locations=[])


def test_dedupes_and_trims_inputs() -> None:
    c = _campaign(categories=[" dentist ", "dentist", "cafe"], locations=["Sydney", "Sydney"])
    assert c.categories == ["dentist", "cafe"]
    assert c.locations == ["Sydney"]


def test_rotation_sweeps_the_whole_grid() -> None:
    c = _campaign()  # 2 categories x 2 locations = 4 cells
    assert c.grid_size == 4
    targets = []
    for _ in range(6):  # more than the grid to prove it wraps
        targets.append(c.current_target())
        c.advance()
    assert targets[:4] == [
        ("dentist", "Sydney"),
        ("orthodontist", "Sydney"),
        ("dentist", "Melbourne"),
        ("orthodontist", "Melbourne"),
    ]
    assert targets[4] == ("dentist", "Sydney")  # wrapped back around


def test_is_due_when_never_run() -> None:
    assert _campaign().is_due() is True


def test_is_due_respects_interval() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    c = _campaign(interval_minutes=60)
    c.last_run_at = now
    assert c.is_due(now + timedelta(minutes=59)) is False
    assert c.is_due(now + timedelta(minutes=60)) is True


def test_inactive_campaign_is_never_due() -> None:
    assert _campaign(is_active=False).is_due() is False
