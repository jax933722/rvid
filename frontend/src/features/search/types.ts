import type { SearchFilter, SearchRequest } from "@/api/types";

export interface SearchFormState {
  text: string;
  industry: string;
  technologies: string[];
  seoMax: string;
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
  industry: "",
  technologies: [],
  seoMax: "",
  flags: {
    has_contact_page: false,
    has_careers_page: false,
    has_blog: false,
    has_ssl: false,
  },
  page: 1,
};

export function toRequest(state: SearchFormState): SearchRequest {
  const filters: SearchFilter[] = [];
  if (state.industry) filters.push({ field: "industry", op: "eq", values: [state.industry] });
  if (state.technologies.length)
    filters.push({ field: "technology", op: "contains", values: state.technologies });
  if (state.seoMax.trim())
    filters.push({ field: "seo_score", op: "lte", values: [state.seoMax.trim()] });
  for (const [field, on] of Object.entries(state.flags)) {
    if (on) filters.push({ field, op: "is_true", values: [] });
  }
  return {
    text: state.text.trim() || null,
    filters,
    facets: ["industry", "technology"],
    page: state.page,
    page_size: 25,
  };
}
