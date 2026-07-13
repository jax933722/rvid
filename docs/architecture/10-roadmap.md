# 10. Future Roadmap — ~50 Development Milestones

Each milestone is scoped to **one coding session**, has a single clear objective, and is
independently testable. **No code is written until each milestone is approved.** Format per
milestone: **Objective · Files · Expected output · Testing checklist · Dependencies.**

Phases: **0** Foundations · **1** Domain · **2** Application/Ports · **3** Infrastructure ·
**4** Crawlers · **5** API · **6** Search · **7** Frontend · **8** Scale/Ops.

> Milestone 0 (this dossier) is complete. Numbering below is 1–50.

---

## Phase 0 — Foundations & Scaffolding

### M1 — Repo scaffolding & tooling
- **Objective:** Create the project skeleton and dev tooling.
- **Files:** `pyproject.toml`, `Makefile`, `.env.example`, `ruff`/`mypy`/`pytest` config, `.pre-commit-config.yaml`, empty package tree under `src/bise/`.
- **Expected output:** `make lint` and `make test` run (0 tests) successfully.
- **Testing checklist:** lint passes; import of `bise` works; pre-commit installs.
- **Dependencies:** M0.

### M2 — Configuration module
- **Objective:** Typed settings via pydantic-settings.
- **Files:** `config/settings.py`, `.env.example` entries.
- **Expected output:** `Settings()` loads/validates; fails fast on bad values.
- **Testing checklist:** unit test valid load, invalid load raises, env override works.
- **Dependencies:** M1.

### M3 — Structured logging
- **Objective:** structlog JSON logging + correlation-id support.
- **Files:** `config/logging.py`, `shared/correlation.py`.
- **Expected output:** JSON log lines with correlation id.
- **Testing checklist:** log capture test asserts JSON keys + correlation propagation.
- **Dependencies:** M2.

### M4 — Docker Compose for local stack
- **Objective:** Postgres + Redis for local dev.
- **Files:** `docker-compose.yml`, `Makefile` targets (`up`, `down`).
- **Expected output:** `make up` starts Postgres + Redis; healthchecks pass.
- **Testing checklist:** containers healthy; app connects to both.
- **Dependencies:** M1.

### M5 — Dependency-rule enforcement
- **Objective:** import-linter contracts for Clean Architecture.
- **Files:** `pyproject.toml` import-linter config, CI step.
- **Expected output:** CI fails if `domain` imports `infrastructure`.
- **Testing checklist:** deliberate violation fails; clean tree passes.
- **Dependencies:** M1.

---

## Phase 1 — Domain Layer

### M6 — Core value objects
- **Objective:** `Url`, `EmailAddress`, `PhoneNumber`, `IndustryCode`, `SeoGrade`.
- **Files:** `domain/value_objects/*.py`, `domain/errors.py`.
- **Expected output:** immutable, self-validating VOs.
- **Testing checklist:** valid construction, invalid rejected, equality-by-value.
- **Dependencies:** M1.

### M7 — Company & Domain entities
- **Objective:** Aggregate root `Company` + `Domain` entity with invariants.
- **Files:** `domain/entities/company.py`, `domain/entities/domain.py`.
- **Expected output:** entities enforce "searchable ⇒ ≥1 domain".
- **Testing checklist:** invariant tests; add/remove domain behavior.
- **Dependencies:** M6.

### M8 — Enrichment entities
- **Objective:** `Technology`, `Contact`, `SeoProfile`, `MarketingSignal`, `Location`.
- **Files:** `domain/entities/*.py`.
- **Expected output:** entities with evidence/confidence fields.
- **Testing checklist:** construction + invariant unit tests.
- **Dependencies:** M6.

### M9 — CrawlJob & Score entities + events
- **Objective:** `CrawlJob` (state machine), `Score`, domain events.
- **Files:** `domain/entities/crawl_job.py`, `domain/entities/score.py`, `domain/events/*.py`.
- **Expected output:** valid job state transitions; events emitted.
- **Testing checklist:** illegal transition rejected; event payloads correct.
- **Dependencies:** M7, M8.

### M10 — Domain services: scoring & classification rules
- **Objective:** `ScoringPolicy`, `ClassificationRules` (pure).
- **Files:** `domain/services/scoring_policy.py`, `domain/services/classification_rules.py`.
- **Expected output:** deterministic score/class from a signal vector.
- **Testing checklist:** table-driven tests over known inputs → outputs.
- **Dependencies:** M8, M9.

---

## Phase 2 — Application Layer (Ports & Use Cases)

### M11 — Repository & gateway ports
- **Objective:** Define all port interfaces + `UnitOfWork`.
- **Files:** `application/ports/repositories.py`, `.../search.py`, `.../fetcher.py`, `.../queue.py`, `.../unit_of_work.py`.
- **Expected output:** abstract interfaces only.
- **Testing checklist:** import + interface shape assertions.
- **Dependencies:** M7–M9.

### M12 — DTOs & query objects
- **Objective:** `SearchQuery`, `Filter`, `CompanySummaryDTO`, `CompanyDetailDTO`.
- **Files:** `application/dto/*.py`.
- **Expected output:** boundary data types.
- **Testing checklist:** serialization/round-trip; validation.
- **Dependencies:** M11.

### M13 — In-memory fakes for ports
- **Objective:** Test doubles for every repository/gateway.
- **Files:** `tests/fakes/*.py`.
- **Expected output:** in-memory repos usable by use-case tests.
- **Testing checklist:** fakes satisfy port contract stubs.
- **Dependencies:** M11.

### M14 — Port contract test suites
- **Objective:** Shared contract tests each implementation must pass.
- **Files:** `tests/contract/*.py`.
- **Expected output:** contract suite runs against fakes (green).
- **Testing checklist:** fakes pass; a broken fake fails.
- **Dependencies:** M13.

### M15 — Query compiler (pure)
- **Objective:** `compile_query(SearchQuery)` → adapter-agnostic plan; filter combination logic.
- **Files:** `application/use_cases/search/compile_query.py`.
- **Expected output:** correct AND/OR composition plan.
- **Testing checklist:** unit tests for within-field OR, cross-field AND, ranges.
- **Dependencies:** M12.

### M16 — SearchCompanies use case
- **Objective:** Orchestrate search against `SearchIndexPort`.
- **Files:** `application/use_cases/search/search_companies.py`.
- **Expected output:** ranked results + facets from a fake index.
- **Testing checklist:** pagination, facet counts, empty result.
- **Dependencies:** M15, M13.

### M17 — GetCompanyDetails use case
- **Objective:** Hydrate a full company DTO.
- **Files:** `application/use_cases/search/get_company_details.py`.
- **Expected output:** aggregated detail DTO or not-found result.
- **Testing checklist:** found/not-found; sub-resources included.
- **Dependencies:** M12, M13.

### M18 — DiscoverBusinesses use case
- **Objective:** Turn a seed into new Company/Domain + enqueue website crawls.
- **Files:** `application/use_cases/discovery/discover_businesses.py`.
- **Expected output:** new entities persisted (fake repo) + jobs enqueued (fake queue).
- **Testing checklist:** dedup, enqueue-per-domain, idempotency.
- **Dependencies:** M13.

### M19 — EnrichCompany orchestration use case
- **Objective:** Fan-out enrichment jobs for a company.
- **Files:** `application/use_cases/enrichment/enrich_company.py`.
- **Expected output:** tech/seo/marketing/location jobs enqueued.
- **Testing checklist:** correct job set emitted; skip already-fresh.
- **Dependencies:** M13.

### M20 — RescoreCompany use case
- **Objective:** Compute + persist scores via `ScoringPolicy`.
- **Files:** `application/use_cases/scoring/rescore_company.py`.
- **Expected output:** Score rows written; event emitted.
- **Testing checklist:** deterministic score; breakdown stored.
- **Dependencies:** M10, M13.

---

## Phase 3 — Infrastructure Layer

### M21 — SQLAlchemy models + Alembic baseline
- **Objective:** ORM tables for all doc-4 entities + initial migration.
- **Files:** `infrastructure/db/models/*.py`, `db/migrations/0001_*.py`, `alembic.ini`.
- **Expected output:** `alembic upgrade head` builds full schema.
- **Testing checklist:** migration up/down; constraints/indexes present.
- **Dependencies:** M4, M7–M9.

### M22 — Company/Domain repositories
- **Objective:** SQLAlchemy impls + Unit of Work.
- **Files:** `infrastructure/db/repositories/company_repository.py`, `.../domain_repository.py`, `.../unit_of_work.py`.
- **Expected output:** CRUD + finders mapping ORM ⇄ entities.
- **Testing checklist:** pass Company/Domain **contract suite** against real Postgres.
- **Dependencies:** M21, M14.

### M23 — Enrichment repositories
- **Objective:** Repos for technologies, seo, marketing, contacts, locations, scores.
- **Files:** `infrastructure/db/repositories/*.py`.
- **Expected output:** persistence for all enrichment facts.
- **Testing checklist:** contract suites pass on Postgres.
- **Dependencies:** M22.

### M24 — CrawlJob repository
- **Objective:** Persist jobs + history; queue-picking finders.
- **Files:** `infrastructure/db/repositories/crawl_job_repository.py`.
- **Expected output:** claim/next/record-history operations.
- **Testing checklist:** concurrent claim safety; history append-only.
- **Dependencies:** M22.

### M25 — Redis/RQ queue adapter
- **Objective:** `QueuePort` impl.
- **Files:** `infrastructure/queue/rq_queue.py`.
- **Expected output:** enqueue/consume with retry+backoff.
- **Testing checklist:** enqueue→consume integration; retry on failure.
- **Dependencies:** M4, M11.

### M26 — HTTP page fetcher (+ robots)
- **Objective:** `PageFetcherPort` via httpx; robots/crawl-delay compliance.
- **Files:** `infrastructure/crawling/httpx_fetcher.py`, `.../robots.py`.
- **Expected output:** polite fetch with rate limiting.
- **Testing checklist:** robots honored; timeout/retry; fixtures via recorded HTTP.
- **Dependencies:** M11.

### M27 — Playwright fetcher (JS pages)
- **Objective:** Alternate `PageFetcherPort` for JS-rendered sites.
- **Files:** `infrastructure/crawling/playwright_fetcher.py`.
- **Expected output:** renders and returns DOM for JS sites.
- **Testing checklist:** contract suite parity with httpx fetcher.
- **Dependencies:** M26.

### M28 — Postgres FTS search adapter
- **Objective:** `SearchIndexPort` over `search_documents` (tsvector + pg_trgm).
- **Files:** `infrastructure/search/postgres_fts.py`, migration for `search_documents`.
- **Expected output:** renders `compile_query` plan → SQL; ranked results + facets.
- **Testing checklist:** pass `SearchIndexPort` **contract suite**; ranking sanity.
- **Dependencies:** M15, M21.

### M29 — Search projection builder
- **Objective:** Rebuild `search_documents` from normalized truth.
- **Files:** `application/use_cases/search/rebuild_search_document.py`, infra wiring.
- **Expected output:** projection updated on enrichment/score change.
- **Testing checklist:** projection matches source; incremental rebuild.
- **Dependencies:** M28, M23.

### M30 — Composition root / DI container
- **Objective:** Wire concrete infra into use cases from config.
- **Files:** `config/containers.py`.
- **Expected output:** fully-wired use cases retrievable for API/workers.
- **Testing checklist:** container builds; swaps by `SEARCH_BACKEND` flag.
- **Dependencies:** M22–M28.

---

## Phase 4 — Crawlers (Workers)

### M31 — BaseCrawler + worker bootstrap
- **Objective:** Shared crawler contract + queue consumer entrypoint.
- **Files:** `crawlers/base.py`, `presentation/workers/worker.py`, `.../handlers.py`.
- **Expected output:** a no-op job runs end-to-end through the worker.
- **Testing checklist:** job dispatch, history recording, error capture.
- **Dependencies:** M24, M25, M30.

### M32 — Website Crawler
- **Objective:** Fetch key pages, store raw + `website_features`.
- **Files:** `crawlers/website_crawler.py`.
- **Expected output:** features persisted; fan-out jobs emitted.
- **Testing checklist:** fixture site → deterministic features; depth/limit honored.
- **Dependencies:** M26, M31, M23.

### M33 — Technology Detection Crawler
- **Objective:** Wappalyzer-rule fingerprinting from stored pages.
- **Files:** `crawlers/technology_crawler.py`, `infrastructure/analyzers/wappalyzer_rules.py`, `scripts/load_wappalyzer_rules.py`.
- **Expected output:** `company_technologies` with confidence.
- **Testing checklist:** HTML fixtures → known tech; version extraction.
- **Dependencies:** M32.

### M34 — SEO Crawler
- **Objective:** Extract + grade SEO signals.
- **Files:** `crawlers/seo_crawler.py`, `infrastructure/analyzers/seo_parser.py`.
- **Expected output:** `seo_profiles` with grade + score.
- **Testing checklist:** fixtures → deterministic grade; sitemap/robots detection.
- **Dependencies:** M32.

### M35 — Marketing Detection Crawler
- **Objective:** Detect pixels/tag managers/CRM/chat tools.
- **Files:** `crawlers/marketing_crawler.py`, `infrastructure/analyzers/marketing_parser.py`.
- **Expected output:** `marketing_signals` rows.
- **Testing checklist:** script-snippet fixtures → detected tools.
- **Dependencies:** M32.

### M36 — Contact Extraction
- **Objective:** Extract emails/phones/socials/addresses.
- **Files:** `infrastructure/analyzers/contact_parser.py`, integrated into website crawler or own step.
- **Expected output:** `contacts` rows with confidence.
- **Testing checklist:** fixtures → precision on emails/phones; dedup.
- **Dependencies:** M32.

### M37 — Location Crawler (open geocoding)
- **Objective:** Resolve + canonicalize locations via Nominatim/OSM.
- **Files:** `crawlers/location_crawler.py`, geocoder adapter behind a port.
- **Expected output:** `locations` + `company_locations`.
- **Testing checklist:** fake geocoder; dedup; rate-limit respected.
- **Dependencies:** M32, M23.

### M38 — Business Classification Crawler
- **Objective:** Rule-based industry + size assignment.
- **Files:** `crawlers/classification_crawler.py`.
- **Expected output:** `companies.industry_id`/`size_bucket` set; triggers scoring.
- **Testing checklist:** signal-vector fixtures → classification.
- **Dependencies:** M10, M33–M37.

### M39 — Business Discovery Crawler
- **Objective:** Ingest from open sources (registries/OSM/directories).
- **Files:** `crawlers/discovery_crawler.py`, source adapters behind a port.
- **Expected output:** new Company/Domain rows; website crawls enqueued.
- **Testing checklist:** fake source fixtures; dedup; idempotency.
- **Dependencies:** M18, M31.

### M40 — Scheduler
- **Objective:** APScheduler recurring jobs (recrawl, refresh, cleanup).
- **Files:** `presentation/scheduler/scheduler.py`.
- **Expected output:** periodic enqueue of due jobs.
- **Testing checklist:** schedule fires; due-selection correct (inject ClockPort).
- **Dependencies:** M24, M25.

---

## Phase 5 — API

### M41 — FastAPI app skeleton + health
- **Objective:** App factory, DI deps, health/readiness.
- **Files:** `presentation/api/main.py`, `.../dependencies.py`, `routers/health.py`, `errors.py`.
- **Expected output:** `/health` + `/health/ready` respond.
- **Testing checklist:** e2e health; readiness checks DB/queue/index.
- **Dependencies:** M30.

### M42 — Search endpoints
- **Objective:** `/search`, `/search/facets`, `/search/suggest`.
- **Files:** `routers/search.py`, `schemas/search.py`.
- **Expected output:** search results + facets over HTTP.
- **Testing checklist:** e2e query→results; filter parsing; pagination.
- **Dependencies:** M16, M28, M41.

### M43 — Company endpoints
- **Objective:** `/companies/{id}` + sub-resources + `enrich`.
- **Files:** `routers/companies.py`, `schemas/company.py`.
- **Expected output:** detail JSON; enrich returns 202 + job handle.
- **Testing checklist:** found/not-found; enrich enqueues.
- **Dependencies:** M17, M19, M41.

### M44 — Crawler/job endpoints
- **Objective:** discovery trigger, job list/detail/retry, crawler stats.
- **Files:** `routers/crawlers.py`, `schemas/crawlers.py`.
- **Expected output:** monitor + control surface.
- **Testing checklist:** trigger 202; list/filter; retry re-enqueues.
- **Dependencies:** M24, M39, M41.

### M45 — Stats & settings endpoints
- **Objective:** `/stats/*`, `/settings`.
- **Files:** `routers/stats.py`, `routers/settings.py`, schemas.
- **Expected output:** overview/tech/industry/pipeline stats; settings read/update.
- **Testing checklist:** aggregate correctness; settings validation.
- **Dependencies:** M41, M23.

### M46 — OpenAPI polish + typed client export
- **Objective:** Finalize schemas, examples; export OpenAPI for the frontend.
- **Files:** router/schema annotations, `scripts/export_openapi.py`.
- **Expected output:** clean OpenAPI JSON; generated TS client stub.
- **Testing checklist:** spec validates; client compiles.
- **Dependencies:** M42–M45.

---

## Phase 6 — Frontend

### M47 — Frontend scaffold + API client + shell
- **Objective:** Vite+TS app, generated API client, app shell/routing.
- **Files:** `frontend/` scaffold, `src/api/`, `src/pages/` shells.
- **Expected output:** app boots; calls `/health`.
- **Testing checklist:** build passes; client hits API; routes render.
- **Dependencies:** M46.

### M48 — Search + Results + Company pages
- **Objective:** Core discovery UX (search → results → detail).
- **Files:** `features/search/*`, `pages/Search|Results|Company`.
- **Expected output:** end-to-end browsing over real API.
- **Testing checklist:** filter round-trip in URL; pagination; detail tabs.
- **Dependencies:** M42, M43, M47.

### M49 — Dashboard, Stats, Crawler Monitor, Settings
- **Objective:** Remaining pages.
- **Files:** `features/stats/*`, `features/crawler/*`, `pages/Dashboard|Statistics|CrawlerMonitor|Settings`.
- **Expected output:** operational + analytical views live.
- **Testing checklist:** charts render; monitor shows jobs; settings save.
- **Dependencies:** M44, M45, M48.

---

## Phase 7 — Scale & Ops

### M50 — OpenSearch adapter + scale hardening
- **Objective:** Implement `OpenSearchAdapter` (same `SearchIndexPort` contract), indexer
  from `search_documents`, shadow-read; add table partitioning plan for
  `company_technologies`/`crawl_history`/`logs`.
- **Files:** `infrastructure/search/opensearch.py`, indexer, `docker-compose` OpenSearch service.
- **Expected output:** `SEARCH_BACKEND=opensearch` serves identical results; business logic unchanged.
- **Testing checklist:** OpenSearch adapter passes the **same contract suite** as FTS;
  shadow-read parity; partition migration up/down.
- **Dependencies:** M28, M29 (and the whole system as validation surface).

---

## How the roadmap honors the architecture

- **Inside-out order** (Domain → Application → Infrastructure → Presentation) means the
  dependency rule is never violated during construction.
- **Contract suites (M14) are written once** and reused for every adapter (M22, M28, M50) —
  this is what makes the FTS→OpenSearch swap a non-event.
- **Every crawler is its own milestone** with fixture-based tests → CI never touches the
  live internet.
- **The scale milestone (M50) changes no business logic** — proof that the design met its
  "scale without rewrite" mandate.

---

**End of architecture dossier. Awaiting approval before Milestone 1.**
