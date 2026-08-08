"""People-extraction port.

Given a company's crawled pages, a person extractor returns the team members it
can identify from public team/about/leadership pages, plus every email address
seen on the site (used to learn the company's email pattern). A rule-based
implementation lives in infrastructure; an ML extractor is a drop-in replacement.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from bise.application.ports.page_content import PageContent

__all__ = ["ExtractedPerson", "PageContent", "PeopleExtraction", "PersonExtractorPort"]


@dataclass(frozen=True, slots=True)
class ExtractedPerson:
    """A raw person parsed from a page (before role/email normalization)."""

    name: str
    title: str | None = None
    email: str | None = None
    source_url: str | None = None


@dataclass(frozen=True, slots=True)
class PeopleExtraction:
    """The people found plus all emails observed across the crawled pages."""

    people: list[ExtractedPerson]
    emails: list[str]


class PersonExtractorPort(Protocol):
    """Extracts people and emails from a company's crawled pages."""

    def extract(self, pages: Sequence[PageContent]) -> PeopleExtraction:
        """Return the people and emails found across the given pages."""
        ...
