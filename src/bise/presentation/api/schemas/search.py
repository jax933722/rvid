"""Request/response schemas for the search API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from bise.application.dto.search_dto import (
    Filter,
    FilterOp,
    SearchQuery,
    SearchResult,
    SortSpec,
)


class FilterRequest(BaseModel):
    """A single structured filter."""

    field: str = Field(..., examples=["technology"])
    op: FilterOp = Field(..., examples=["contains"])
    values: list[str] = Field(default_factory=list, examples=[["WordPress"]])

    def to_domain(self) -> Filter:
        return Filter(field=self.field, op=self.op, values=tuple(self.values))


class SortRequest(BaseModel):
    """Result ordering."""

    field: str = "relevance"
    descending: bool = True

    def to_domain(self) -> SortSpec:
        return SortSpec(field=self.field, descending=self.descending)


class SearchRequest(BaseModel):
    """Request body for ``POST /search``."""

    text: str | None = Field(default=None, examples=["dentist"])
    filters: list[FilterRequest] = Field(default_factory=list)
    facets: list[str] = Field(default_factory=list, examples=[["industry", "technology"]])
    sort: SortRequest = Field(default_factory=SortRequest)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=200)

    def to_query(self) -> SearchQuery:
        return SearchQuery(
            text=self.text,
            filters=tuple(f.to_domain() for f in self.filters),
            facets=tuple(self.facets),
            sort=self.sort.to_domain(),
            page=self.page,
            page_size=self.page_size,
        )


class SearchItemResponse(BaseModel):
    """One company in the result page."""

    company_id: int
    display_name: str
    primary_domain: str | None
    industry: str | None
    country: str | None
    state: str | None
    city: str | None
    size_bucket: str | None
    founded_year: int | None
    employee_count: int | None
    seo_score: float | None
    seo_grade: str | None
    technologies: list[str]


class FacetValueResponse(BaseModel):
    """A facet bucket."""

    value: str
    count: int


class SearchResponse(BaseModel):
    """A page of search results with facets."""

    items: list[SearchItemResponse]
    facets: dict[str, list[FacetValueResponse]]
    total: int
    page: int
    page_size: int

    @classmethod
    def from_result(cls, result: SearchResult) -> SearchResponse:
        return cls(
            items=[
                SearchItemResponse(
                    company_id=i.company_id,
                    display_name=i.display_name,
                    primary_domain=i.primary_domain,
                    industry=i.industry,
                    country=i.country,
                    state=i.state,
                    city=i.city,
                    size_bucket=i.size_bucket,
                    founded_year=i.founded_year,
                    employee_count=i.employee_count,
                    seo_score=i.seo_score,
                    seo_grade=i.seo_grade,
                    technologies=i.technologies,
                )
                for i in result.items
            ],
            facets={
                field: [FacetValueResponse(value=v.value, count=v.count) for v in buckets]
                for field, buckets in result.facets.items()
            },
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
