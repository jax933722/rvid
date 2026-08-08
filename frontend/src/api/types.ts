// TypeScript mirror of the backend's API schemas. Kept in one place so the
// frontend has a single source of truth for the wire contract.

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface DomainResponse {
  id: number | null;
  hostname: string;
  is_primary: boolean;
  crawl_status: string;
}

export interface Company {
  id: number | null;
  display_name: string;
  legal_name: string | null;
  status: string;
  industry: string | null;
  size_bucket: string | null;
  country: string | null;
  state: string | null;
  city: string | null;
  founded_year: number | null;
  employee_count: number | null;
  contact_email: string | null;
  contact_phone: string | null;
  domains: DomainResponse[];
  created_at: string;
  updated_at: string;
}

export interface CrawlJob {
  id: number | null;
  domain_id: number;
  hostname: string;
  job_type: string;
  status: string;
  attempts: number;
  pages_crawled: number;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface Technology {
  id: number | null;
  name: string;
  category: string;
  vendor: string | null;
}

export interface CompanyTechnology {
  name: string;
  category: string;
  confidence: number;
  evidence: string;
  version: string | null;
  detected_at: string;
}

export interface SeoProfile {
  url: string;
  score: number;
  grade: string;
  title: string | null;
  meta_description: string | null;
  canonical: string | null;
  is_indexable: boolean;
  h1_count: number;
  h2_count: number;
  has_open_graph: boolean;
  has_structured_data: boolean;
  has_ssl: boolean;
  images_total: number;
  images_missing_alt: number;
  internal_links: number;
  external_links: number;
  word_count: number;
  scanned_at: string;
}

export type FilterOp = "eq" | "in" | "gte" | "lte" | "between" | "contains" | "is_true";

export interface SearchFilter {
  field: string;
  op: FilterOp;
  values: string[];
}

export interface SearchRequest {
  text?: string | null;
  filters: SearchFilter[];
  facets: string[];
  sort?: { field: string; descending: boolean };
  page: number;
  page_size: number;
}

export interface SearchItem {
  company_id: number;
  display_name: string;
  primary_domain: string | null;
  industry: string | null;
  country: string | null;
  state: string | null;
  city: string | null;
  size_bucket: string | null;
  founded_year: number | null;
  employee_count: number | null;
  seo_score: number | null;
  seo_grade: string | null;
  technologies: string[];
}

export interface FacetValue {
  value: string;
  count: number;
}

export interface SearchResult {
  items: SearchItem[];
  facets: Record<string, FacetValue[]>;
  total: number;
  page: number;
  page_size: number;
}

export interface SavedSearch {
  id: number;
  name: string;
  query: SearchRequest;
  created_at: string;
  updated_at: string;
}

export interface CompanyList {
  id: number;
  name: string;
  description: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface CompanyTag {
  id: number;
  company_id: number;
  label: string;
  created_at: string;
}

export interface Person {
  id: number | null;
  company_id: number;
  name: string;
  title: string | null;
  role_category: string;
  email: string | null;
  email_status: string; // "published" | "guessed" | "none"
  source_url: string | null;
}

export interface Workspace {
  id: number | null;
  name: string;
  slug: string;
  created_at: string;
}

export interface ApiKey {
  id: number | null;
  workspace_id: number;
  name: string;
  prefix: string;
  revoked: boolean;
  last_used_at: string | null;
  created_at: string;
}

export interface CreatedApiKey {
  api_key: ApiKey;
  secret: string;
}

export interface EnrichmentJob {
  id: number | null;
  company_id: number;
  status: string;
  attempts: number;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface EnqueueResult {
  enqueued: number;
  skipped: number;
  jobs: EnrichmentJob[];
}

export interface QueueSummary {
  counts: Record<string, number>;
  recent: EnrichmentJob[];
}

export interface LeadCampaign {
  id: number | null;
  name: string;
  categories: string[];
  locations: string[];
  interval_minutes: number;
  is_active: boolean;
  auto_enrich: boolean;
  per_run_limit: number;
  lead_count: number;
  grid_size: number;
  next_category: string;
  next_location: string;
  last_run_at: string | null;
  created_at: string;
}

export interface CampaignRunResult {
  campaign_id: number;
  category: string;
  location: string;
  found: number;
  new_leads: number;
  enqueued_enrichment: number;
}

export interface Lead {
  id: number | null;
  campaign_id: number;
  status: string;
  created_at: string;
  company: Company;
}

export interface CreateCampaignBody {
  name: string;
  categories: string[];
  locations: string[];
  interval_minutes?: number;
  auto_enrich?: boolean;
  per_run_limit?: number;
}

export interface DiscoveredBusiness {
  name: string;
  category: string;
  website: string | null;
  website_url: string | null;
  phone: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  postal_code: string | null;
  latitude: number | null;
  longitude: number | null;
  source_url: string | null;
  company_id: number | null;
}
