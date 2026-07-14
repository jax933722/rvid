"""Canonical export columns and row projections.

One column vocabulary is shared by every export source (search results and list
members) so downloads are consistent regardless of where they were triggered.
"""

from __future__ import annotations

from collections.abc import Mapping

from bise.application.dto.company_dto import CompanyDTO
from bise.application.dto.search_dto import SearchResultItem

# Ordered, human-friendly export columns. Sources fill what they know; anything
# unavailable for a given source is left blank.
EXPORT_COLUMNS: tuple[str, ...] = (
    "company_id",
    "display_name",
    "website",
    "industry",
    "country",
    "state",
    "city",
    "size_bucket",
    "founded_year",
    "employee_count",
    "seo_grade",
    "seo_score",
    "technologies",
    "contact_email",
    "contact_phone",
)


def search_item_to_row(item: SearchResultItem) -> Mapping[str, object]:
    """Project a search result into an export row."""
    return {
        "company_id": item.company_id,
        "display_name": item.display_name,
        "website": item.primary_domain,
        "industry": item.industry,
        "country": item.country,
        "state": item.state,
        "city": item.city,
        "size_bucket": item.size_bucket,
        "founded_year": item.founded_year,
        "employee_count": item.employee_count,
        "seo_grade": item.seo_grade,
        "seo_score": item.seo_score,
        "technologies": "; ".join(item.technologies),
        "contact_email": None,
        "contact_phone": None,
    }


def company_to_row(company: CompanyDTO) -> Mapping[str, object]:
    """Project a company detail DTO into an export row."""
    primary = next((d.hostname for d in company.domains if d.is_primary), None)
    if primary is None and company.domains:
        primary = company.domains[0].hostname
    return {
        "company_id": company.id,
        "display_name": company.display_name,
        "website": primary,
        "industry": company.industry,
        "country": company.country,
        "state": company.state,
        "city": company.city,
        "size_bucket": company.size_bucket,
        "founded_year": company.founded_year,
        "employee_count": company.employee_count,
        "seo_grade": None,
        "seo_score": None,
        "technologies": None,
        "contact_email": company.contact_email,
        "contact_phone": company.contact_phone,
    }
