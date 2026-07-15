"""Pure helpers for people/role/email inference (no I/O, unit-tested directly).

* ``classify_role`` maps a free-text job title to a normalized RoleCategory.
* ``infer_email_pattern`` learns a company's email format from a known
  name/email pair (e.g. "Jane Doe" + "jane.doe@acme.com" -> "{first}.{last}").
* ``apply_email_pattern`` renders that pattern for another person on the same
  domain, so a published email for one person can fill gaps for colleagues —
  grounded in observed evidence, not blind guessing.
"""

from __future__ import annotations

import re

from bise.domain.entities.person import RoleCategory

# Ordered most-specific/senior first: the first keyword found wins, so
# "Founder & CEO" classifies as FOUNDER and "VP of Engineering" as VP.
_ROLE_RULES: tuple[tuple[RoleCategory, tuple[str, ...]], ...] = (
    (RoleCategory.FOUNDER, ("founder", "co-founder", "cofounder")),
    (RoleCategory.CEO, ("ceo", "chief executive", "managing director", "president")),
    (RoleCategory.CTO, ("cto", "chief technology", "chief technical")),
    (RoleCategory.CFO, ("cfo", "chief financial")),
    (RoleCategory.COO, ("coo", "chief operating")),
    (RoleCategory.CMO, ("cmo", "chief marketing")),
    (RoleCategory.VP, ("vp", "vice president", "svp", "evp")),
    (RoleCategory.HEAD, ("head of", "head")),
    (RoleCategory.DIRECTOR, ("director",)),
    (RoleCategory.MANAGER, ("manager", "lead")),
)

_LOCAL = r"[a-z0-9][a-z0-9._%+-]*"
_EMAIL_RE = re.compile(rf"{_LOCAL}@[a-z0-9.-]+\.[a-z]{{2,}}", re.IGNORECASE)


def classify_role(title: str | None) -> RoleCategory:
    """Map a job title to a RoleCategory (``OTHER`` when nothing matches).

    Keywords match on word boundaries so short acronyms don't match inside
    longer words (e.g. "cto" must not fire on "dire**cto**r").
    """
    if not title:
        return RoleCategory.OTHER
    lowered = title.lower()
    for category, keywords in _ROLE_RULES:
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                return category
    return RoleCategory.OTHER


def find_emails(text: str) -> list[str]:
    """Return all distinct email addresses in ``text`` (lowercased, in order)."""
    seen: dict[str, None] = {}
    for match in _EMAIL_RE.findall(text or ""):
        seen.setdefault(match.lower(), None)
    return list(seen)


def _name_parts(name: str) -> tuple[str, str]:
    """Return (first, last); ``last`` is empty for single-token names."""
    parts = [re.sub(r"[^a-z]", "", p.lower()) for p in name.split()]
    parts = [p for p in parts if p]
    if len(parts) < 2:
        return (parts[0] if parts else ""), ""
    return parts[0], parts[-1]


def infer_email_pattern(name: str, email: str) -> str | None:
    """Infer a ``{first}``/``{last}``/``{f}`` local-part template from a pair.

    Returns e.g. ``"{first}.{last}"`` or ``"{f}{last}"``; ``None`` if the email's
    local part doesn't correspond to the person's name.
    """
    if "@" not in email:
        return None
    local = email.split("@", 1)[0].lower()
    first, last = _name_parts(name)
    if not first or not last:
        return None

    separators = ["", ".", "_", "-"]
    for sep in separators:
        if local == f"{first}{sep}{last}":
            return f"{{first}}{sep}{{last}}"
        if local == f"{first[0]}{sep}{last}":
            return f"{{f}}{sep}{{last}}"
        if local == f"{first}{sep}{last[0]}":
            return f"{{first}}{sep}{{l}}"
    if local == first:
        return "{first}"
    if local == last:
        return "{last}"
    return None


def apply_email_pattern(name: str, domain: str, pattern: str) -> str | None:
    """Render ``pattern`` for ``name`` at ``domain`` (``None`` if name is unusable)."""
    first, last = _name_parts(name)
    if not first or not last:
        return None
    local = (
        pattern.replace("{first}", first)
        .replace("{last}", last)
        .replace("{f}", first[0])
        .replace("{l}", last[0])
    )
    return f"{local}@{domain.lower()}"
