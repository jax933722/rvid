"""Unit tests for the rule-based team extractor."""

from __future__ import annotations

from bise.application.ports.person_extractor import PageContent
from bise.infrastructure.analyzers.team_extractor import RuleBasedTeamExtractor

JSONLD = """
<html><head><script type="application/ld+json">
{"@context":"https://schema.org","@type":"Person","name":"Jane Doe",
 "jobTitle":"Founder & CEO","email":"mailto:jane.doe@acme.com"}
</script></head><body></body></html>
"""

CARDS = """
<html><body>
<div class="team-member">
  <h3>John Smith</h3>
  <p class="role">Chief Technology Officer</p>
  <a href="mailto:john@acme.com">email</a>
</div>
<div class="team-member">
  <h3>Mary Jones</h3>
  <span class="title">Head of Marketing</span>
</div>
<div class="footer">Call us on 1300 000 000 — info@acme.com</div>
</body></html>
"""


def test_extracts_person_from_jsonld() -> None:
    result = RuleBasedTeamExtractor().extract(
        [PageContent(url="https://acme.com/about", html=JSONLD)]
    )
    assert len(result.people) == 1
    person = result.people[0]
    assert person.name == "Jane Doe"
    assert person.title == "Founder & CEO"
    assert person.email == "jane.doe@acme.com"
    assert "jane.doe@acme.com" in result.emails


def test_extracts_people_from_team_cards() -> None:
    result = RuleBasedTeamExtractor().extract(
        [PageContent(url="https://acme.com/team", html=CARDS)]
    )
    by_name = {p.name: p for p in result.people}
    assert set(by_name) == {"John Smith", "Mary Jones"}
    assert by_name["John Smith"].title == "Chief Technology Officer"
    assert by_name["John Smith"].email == "john@acme.com"
    assert by_name["Mary Jones"].title == "Head of Marketing"
    # All page emails are collected (for pattern inference).
    assert "info@acme.com" in result.emails


def test_ignores_non_person_headings() -> None:
    html = "<div class='team-member'><h3>Our Amazing Award Winning Team Today</h3></div>"
    result = RuleBasedTeamExtractor().extract([PageContent(url="https://x.com", html=html)])
    assert result.people == []  # too many words to be a name
