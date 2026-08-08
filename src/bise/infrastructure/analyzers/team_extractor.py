"""``RuleBasedTeamExtractor`` — find team members on public team/about pages.

Two complementary strategies, both using only what the company publishes:

1. **JSON-LD** ``schema.org/Person`` objects (name + jobTitle + email) — the
   clean, structured path many sites already expose.
2. **Team cards** — DOM blocks whose class/itemtype looks like a person card
   (``team-member``, ``profile``, ``itemtype=...Person``); within each, the name
   is the first heading and the title is a role-ish element or line.

All emails on the page (``mailto:`` + inline text) are collected so the
application layer can learn the company's email pattern. No LinkedIn, no paid
data.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence

from bs4 import BeautifulSoup, Tag

from bise.application.ports.person_extractor import (
    ExtractedPerson,
    PageContent,
    PeopleExtraction,
)
from bise.domain.services.people import classify_role, find_emails

_CARD_HINTS = ("team-member", "team_member", "teammember", "team-card", "staff", "profile", "bio")
_NAME_TAGS = ("h1", "h2", "h3", "h4", "h5", "strong", "b")
_TITLE_CLASS_HINTS = ("title", "role", "position", "job")
# A parsed name should look like a person's name, not a sentence or a heading.
_MAX_NAME_WORDS = 4


def _classes(tag: Tag) -> str:
    value = tag.get("class")
    if isinstance(value, list):
        return " ".join(value).lower()
    return str(value or "").lower()


def _looks_like_name(text: str) -> bool:
    words = text.split()
    if not (1 < len(words) <= _MAX_NAME_WORDS):
        return False
    return all(any(c.isalpha() for c in w) for w in words) and not any(c.isdigit() for c in text)


class RuleBasedTeamExtractor:
    """Extracts people + emails from crawled pages (bs4 + lxml, no network)."""

    def extract(self, pages: Sequence[PageContent]) -> PeopleExtraction:
        found: dict[str, ExtractedPerson] = {}
        emails: dict[str, None] = {}

        for page in pages:
            soup = BeautifulSoup(page.html or "", "lxml")
            for email in find_emails(soup.get_text(" ")):
                emails.setdefault(email, None)
            for email in self._mailto_emails(soup):
                emails.setdefault(email, None)

            for person in self._from_jsonld(soup, page.url):
                found.setdefault(person.name.lower(), person)
            for person in self._from_cards(soup, page.url):
                found.setdefault(person.name.lower(), person)

        # Any email attached to a person also feeds pattern inference.
        for person in found.values():
            if person.email:
                emails.setdefault(person.email, None)

        return PeopleExtraction(people=list(found.values()), emails=list(emails))

    # --- strategies --------------------------------------------------------
    @staticmethod
    def _mailto_emails(soup: Tag) -> Iterable[str]:
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"])
            if href.lower().startswith("mailto:"):
                yield href[7:].split("?", 1)[0].strip().lower()

    def _from_jsonld(self, soup: BeautifulSoup, url: str) -> Iterable[ExtractedPerson]:
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(script.string or "")
            except (ValueError, TypeError):
                continue
            for node in self._iter_nodes(data):
                if not isinstance(node, dict):
                    continue
                types = node.get("@type", "")
                type_str = " ".join(types) if isinstance(types, list) else str(types)
                name = node.get("name")
                if "Person" in type_str and isinstance(name, str) and _looks_like_name(name):
                    email = node.get("email")
                    if isinstance(email, str) and email.lower().startswith("mailto:"):
                        email = email[7:]
                    job_title = node.get("jobTitle")
                    yield ExtractedPerson(
                        name=name.strip(),
                        title=job_title if isinstance(job_title, str) else None,
                        email=email.strip().lower() if isinstance(email, str) else None,
                        source_url=url,
                    )

    @staticmethod
    def _iter_nodes(data: object) -> Iterable[object]:
        if isinstance(data, list):
            for item in data:
                yield from RuleBasedTeamExtractor._iter_nodes(item)
        elif isinstance(data, dict):
            yield data
            graph = data.get("@graph")
            if isinstance(graph, list):
                for item in graph:
                    yield from RuleBasedTeamExtractor._iter_nodes(item)

    def _from_cards(self, soup: BeautifulSoup, url: str) -> Iterable[ExtractedPerson]:
        candidates: list[Tag] = []
        for tag in soup.find_all(True):
            if not isinstance(tag, Tag):
                continue
            itemtype = str(tag.get("itemtype") or "").lower()
            if any(hint in _classes(tag) for hint in _CARD_HINTS) or "person" in itemtype:
                candidates.append(tag)

        for card in candidates:
            name = self._card_name(card)
            if name is None:
                continue
            yield ExtractedPerson(
                name=name,
                title=self._card_title(card),
                email=next(iter(self._mailto_emails(card)), None),
                source_url=url,
            )

    @staticmethod
    def _card_name(card: Tag) -> str | None:
        for tag_name in _NAME_TAGS:
            heading = card.find(tag_name)
            if isinstance(heading, Tag):
                text = heading.get_text(" ", strip=True)
                if _looks_like_name(text):
                    return text
        return None

    @staticmethod
    def _card_title(card: Tag) -> str | None:
        for element in card.find_all(["p", "span", "div", "h6"]):
            if not isinstance(element, Tag):
                continue
            if any(hint in _classes(element) for hint in _TITLE_CLASS_HINTS):
                text = element.get_text(" ", strip=True)
                if text:
                    return text
        # Fall back to the first line that classifies as a real role.
        for element in card.find_all(["p", "span", "div", "h6"]):
            text = element.get_text(" ", strip=True)
            if text and classify_role(text).value != "other":
                return text
        return None
