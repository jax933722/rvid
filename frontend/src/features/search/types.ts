import type { SearchFilter, SearchRequest } from "@/api/types";

export interface RangeState {
  min: string;
  max: string;
}

const EMPTY_RANGE: RangeState = { min: "", max: "" };

export interface SearchFormState {
  text: string;
  industries: string[];
  country: string;
  state: string;
  city: string;
  technologies: string[];
  founded: RangeState;
  employees: RangeState;
  seoGrades: string[];
  seo: RangeState;
  flags: {
    has_contact_page: boolean;
    has_careers_page: boolean;
    has_blog: boolean;
    has_ssl: boolean;
  };
  page: number;
}

export const EMPTY_STATE: SearchFormState = {
  text: "",
  industries: [],
  country: "",
  state: "",
  city: "",
  technologies: [],
  founded: { ...EMPTY_RANGE },
  employees: { ...EMPTY_RANGE },
  seoGrades: [],
  seo: { ...EMPTY_RANGE },
  flags: {
    has_contact_page: false,
    has_careers_page: false,
    has_blog: false,
    has_ssl: false,
  },
  page: 1,
};

/** The facets the Prospector rail renders as clickable suggestion chips. */
export const FACET_FIELDS = ["industry", "technology", "country", "city", "size_bucket"];

/** Turn a min/max range into the tightest valid numeric filter (between / gte / lte). */
function rangeFilter(field: string, range: RangeState): SearchFilter | null {
  const min = range.min.trim();
  const max = range.max.trim();
  if (min && max) return { field, op: "between", values: [min, max] };
  if (min) return { field, op: "gte", values: [min] };
  if (max) return { field, op: "lte", values: [max] };
  return null;
}

/** Count the active filter groups — drives the "N filters" badge in the header. */
export function activeFilterCount(state: SearchFormState): number {
  let n = 0;
  if (state.text.trim()) n++;
  if (state.industries.length) n++;
  if (state.country.trim()) n++;
  if (state.state.trim()) n++;
  if (state.city.trim()) n++;
  if (state.technologies.length) n++;
  if (state.founded.min.trim() || state.founded.max.trim()) n++;
  if (state.employees.min.trim() || state.employees.max.trim()) n++;
  if (state.seoGrades.length) n++;
  if (state.seo.min.trim() || state.seo.max.trim()) n++;
  n += Object.values(state.flags).filter(Boolean).length;
  return n;
}

export function toRequest(state: SearchFormState): SearchRequest {
  const filters: SearchFilter[] = [];

  if (state.industries.length)
    filters.push({ field: "industry", op: "in", values: state.industries });
  if (state.country.trim()) filters.push({ field: "country", op: "eq", values: [state.country.trim()] });
  if (state.state.trim()) filters.push({ field: "state", op: "eq", values: [state.state.trim()] });
  if (state.city.trim()) filters.push({ field: "city", op: "eq", values: [state.city.trim()] });

  if (state.technologies.length)
    filters.push({ field: "technology", op: "contains", values: state.technologies });

  const founded = rangeFilter("founded_year", state.founded);
  if (founded) filters.push(founded);
  const employees = rangeFilter("employee_count", state.employees);
  if (employees) filters.push(employees);

  if (state.seoGrades.length)
    filters.push({ field: "seo_grade", op: "in", values: state.seoGrades });
  const seo = rangeFilter("seo_score", state.seo);
  if (seo) filters.push(seo);

  for (const [field, on] of Object.entries(state.flags)) {
    if (on) filters.push({ field, op: "is_true", values: [] });
  }

  return {
    text: state.text.trim() || null,
    filters,
    facets: FACET_FIELDS,
    page: state.page,
    page_size: 25,
  };
}
