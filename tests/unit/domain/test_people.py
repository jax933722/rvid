"""Unit tests for the Person entity and people/role/email services."""

from __future__ import annotations

import pytest

from bise.domain.entities.person import EmailStatus, Person, RoleCategory
from bise.domain.errors import InvalidValueError
from bise.domain.services.people import (
    apply_email_pattern,
    classify_role,
    find_emails,
    infer_email_pattern,
)


def test_person_requires_name_and_normalizes() -> None:
    with pytest.raises(InvalidValueError):
        Person(company_id=1, name="  ")
    p = Person(company_id=1, name="  Jane   Doe ", email="JANE@ACME.COM ")
    assert p.name == "Jane Doe"
    assert p.email == "jane@acme.com"


def test_person_without_email_forces_status_none() -> None:
    p = Person(company_id=1, name="Jane", email=None, email_status=EmailStatus.PUBLISHED)
    assert p.email_status is EmailStatus.NONE


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Founder & CEO", RoleCategory.FOUNDER),
        ("Chief Executive Officer", RoleCategory.CEO),
        ("CTO", RoleCategory.CTO),
        ("VP of Engineering", RoleCategory.VP),
        ("Head of Marketing", RoleCategory.HEAD),
        ("Regional Director", RoleCategory.DIRECTOR),
        ("Office Manager", RoleCategory.MANAGER),
        ("Dental Hygienist", RoleCategory.OTHER),
        (None, RoleCategory.OTHER),
    ],
)
def test_classify_role(title: str | None, expected: RoleCategory) -> None:
    assert classify_role(title) == expected


def test_find_emails_dedupes_in_order() -> None:
    text = "Contact info@acme.com or SALES@acme.com or info@acme.com"
    assert find_emails(text) == ["info@acme.com", "sales@acme.com"]


@pytest.mark.parametrize(
    ("name", "email", "pattern"),
    [
        ("Jane Doe", "jane.doe@acme.com", "{first}.{last}"),
        ("Jane Doe", "jdoe@acme.com", "{f}{last}"),
        ("Jane Doe", "jane@acme.com", "{first}"),
        ("Jane Doe", "jane_doe@acme.com", "{first}_{last}"),
    ],
)
def test_infer_email_pattern(name: str, email: str, pattern: str) -> None:
    assert infer_email_pattern(name, email) == pattern


def test_infer_email_pattern_none_when_unrelated() -> None:
    assert infer_email_pattern("Jane Doe", "hello@acme.com") is None


def test_apply_email_pattern() -> None:
    assert apply_email_pattern("John Smith", "acme.com", "{first}.{last}") == "john.smith@acme.com"
    assert apply_email_pattern("John Smith", "acme.com", "{f}{last}") == "jsmith@acme.com"
    assert apply_email_pattern("Cher", "acme.com", "{first}.{last}") is None  # no last name
