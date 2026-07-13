// Typed client for the Search API. The only place the frontend talks HTTP.

import type {
  Company,
  CompanyTechnology,
  CrawlJob,
  Page,
  SearchRequest,
  SearchResult,
  SeoProfile,
  Technology,
} from "./types";

const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  listCompanies: (page = 1, pageSize = 25) =>
    request<Page<Company>>(`/companies?page=${page}&page_size=${pageSize}`),

  getCompany: (id: number) => request<Company>(`/companies/${id}`),

  search: (body: SearchRequest) =>
    request<SearchResult>("/search", { method: "POST", body: JSON.stringify(body) }),

  listTechnologies: (page = 1, pageSize = 200) =>
    request<Page<Technology>>(`/technologies?page=${page}&page_size=${pageSize}`),

  companyTechnologies: (id: number) =>
    request<CompanyTechnology[]>(`/companies/${id}/technologies`),

  companySeo: (id: number) => request<SeoProfile>(`/companies/${id}/seo`),

  listCrawlJobs: (page = 1, pageSize = 25, status?: string) =>
    request<Page<CrawlJob>>(
      `/crawlers/jobs?page=${page}&page_size=${pageSize}${status ? `&status=${status}` : ""}`,
    ),

  requestCrawl: (hostname: string) =>
    request<CrawlJob>("/crawl", { method: "POST", body: JSON.stringify({ hostname }) }),

  reindexCompany: (id: number) =>
    request<{ status: string }>(`/companies/${id}/index`, { method: "POST" }),
};
