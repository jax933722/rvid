// Typed client for the Search API. The only place the frontend talks HTTP.

import type {
  ApiKey,
  Company,
  CompanyList,
  CompanyTag,
  CompanyTechnology,
  CrawlJob,
  CreatedApiKey,
  DiscoveredBusiness,
  EnqueueResult,
  Page,
  Person,
  QueueSummary,
  SavedSearch,
  SearchRequest,
  SearchResult,
  SeoProfile,
  Technology,
  Workspace,
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

export type ExportFormat = "csv" | "json" | "xlsx";

/** Fetch a binary payload and trigger a browser download using its filename. */
async function download(path: string, init?: RequestInit): Promise<void> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new ApiError(res.status, res.statusText);
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const filename = /filename="?([^"]+)"?/.exec(disposition)?.[1] ?? "export";
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
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

  companyPeople: (id: number) => request<Person[]>(`/companies/${id}/people`),

  listCrawlJobs: (page = 1, pageSize = 25, status?: string) =>
    request<Page<CrawlJob>>(
      `/crawlers/jobs?page=${page}&page_size=${pageSize}${status ? `&status=${status}` : ""}`,
    ),

  requestCrawl: (hostname: string) =>
    request<CrawlJob>("/crawl", { method: "POST", body: JSON.stringify({ hostname }) }),

  reindexCompany: (id: number) =>
    request<{ status: string }>(`/companies/${id}/index`, { method: "POST" }),

  discover: (category: string, location: string, limit = 50) =>
    request<DiscoveredBusiness[]>("/discover", {
      method: "POST",
      body: JSON.stringify({ category, location, limit }),
    }),

  enrichCompany: (id: number) =>
    request<{ status: string; company_id: number }>(`/companies/${id}/enrich`, { method: "POST" }),

  // --- workspace: saved searches ---
  listSavedSearches: () => request<SavedSearch[]>("/saved-searches"),

  saveSearch: (name: string, query: SearchRequest) =>
    request<SavedSearch>("/saved-searches", {
      method: "POST",
      body: JSON.stringify({ name, query }),
    }),

  deleteSavedSearch: (id: number) =>
    request<void>(`/saved-searches/${id}`, { method: "DELETE" }),

  // --- workspace: lists ---
  listLists: () => request<CompanyList[]>("/lists"),

  createList: (name: string, description?: string | null) =>
    request<CompanyList>("/lists", {
      method: "POST",
      body: JSON.stringify({ name, description: description ?? null }),
    }),

  deleteList: (id: number) => request<void>(`/lists/${id}`, { method: "DELETE" }),

  listMembers: (id: number) => request<Company[]>(`/lists/${id}/companies`),

  addToList: (listId: number, companyId: number) =>
    request<CompanyList>(`/lists/${listId}/companies`, {
      method: "POST",
      body: JSON.stringify({ company_id: companyId }),
    }),

  removeFromList: (listId: number, companyId: number) =>
    request<void>(`/lists/${listId}/companies/${companyId}`, { method: "DELETE" }),

  // --- workspace: tags ---
  listTags: (companyId: number) => request<CompanyTag[]>(`/companies/${companyId}/tags`),

  addTag: (companyId: number, label: string) =>
    request<CompanyTag>(`/companies/${companyId}/tags`, {
      method: "POST",
      body: JSON.stringify({ label }),
    }),

  removeTag: (companyId: number, label: string) =>
    request<void>(`/companies/${companyId}/tags/${encodeURIComponent(label)}`, {
      method: "DELETE",
    }),

  // --- export (triggers a file download) ---
  exportSearch: (body: SearchRequest, format: ExportFormat) =>
    download(`/export/search?format=${format}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  exportListMembers: (listId: number, format: ExportFormat) =>
    download(`/export/lists/${listId}?format=${format}`),

  // --- enrichment queue ---
  enqueueEnrichment: (body: { company_ids?: number[]; list_id?: number }) =>
    request<EnqueueResult>("/enrichment/jobs", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  enrichmentQueue: () => request<QueueSummary>("/enrichment/queue"),

  runEnrichment: (maxJobs = 10) =>
    request<{ processed: number }>(`/enrichment/run?max_jobs=${maxJobs}`, { method: "POST" }),

  // --- auth: current workspace + API keys ---
  whoami: () => request<Workspace>("/auth/whoami"),

  listApiKeys: () => request<ApiKey[]>("/api-keys"),

  createApiKey: (name: string) =>
    request<CreatedApiKey>("/api-keys", { method: "POST", body: JSON.stringify({ name }) }),

  revokeApiKey: (id: number) => request<void>(`/api-keys/${id}`, { method: "DELETE" }),
};
