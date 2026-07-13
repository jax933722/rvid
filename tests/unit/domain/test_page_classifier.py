"""Unit tests for the page-type classifier."""

from __future__ import annotations

import pytest

from bise.domain.entities.crawled_page import PageType
from bise.domain.services.page_classifier import classify_page_type


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://acme.com/", PageType.HOME),
        ("https://acme.com/about-us", PageType.ABOUT),
        ("https://acme.com/contact", PageType.CONTACT),
        ("https://acme.com/careers/engineer", PageType.CAREERS),
        ("https://acme.com/jobs", PageType.CAREERS),
        ("https://acme.com/blog/post-1", PageType.BLOG),
        ("https://acme.com/privacy-policy", PageType.PRIVACY),
        ("https://acme.com/terms", PageType.TERMS),
        ("https://acme.com/products/widget", PageType.OTHER),
    ],
)
def test_classification(url: str, expected: PageType) -> None:
    assert classify_page_type(url) is expected


def test_is_home_flag_forces_home() -> None:
    assert classify_page_type("https://acme.com/anything", is_home=True) is PageType.HOME
