# 3. Folder Structure

The layout is **layer-first inside a domain-oriented package**, so the Clean Architecture
boundaries are visible on disk. Import direction is enforceable (a linter rule can forbid
`domain` from importing `infrastructure`).

```
bi-search-engine/
├── README.md
├── pyproject.toml                # single source of deps + tooling config
├── .env.example                  # documented env vars (no secrets committed)
├── docker-compose.yml            # postgres, redis, api, worker, frontend for localhost
├── Makefile                      # make test / lint / run / migrate — one-word ops
├── alembic.ini                   # migration config
│
├── docs/
│   └── architecture/             # THIS dossier — design of record
│
├── config/
│   ├── settings.py               # pydantic-settings: typed, validated config
│   ├── logging.py                # structlog setup (JSON, correlation ids)
│   └── containers.py             # composition root / DI wiring
│
├── src/
│   └── bise/                     # the installable package (Business Intelligence Search Engine)
│       │
│       ├── domain/               # LAYER 1 — pure business, zero framework imports
│       │   ├── entities/         #   Company, Domain, Technology, Contact, CrawlJob, Score
│       │   ├── value_objects/    #   Url, EmailAddress, PhoneNumber, IndustryCode, SeoGrade
│       │   ├── services/         #   ScoringPolicy, ClassificationRules (cross-entity logic)
│       │   ├── events/           #   CompanyDiscovered, WebsiteCrawled, TechnologyDetected
│       │   └── errors.py         #   domain-level exceptions (invariant violations)
│       │
│       ├── application/          # LAYER 2 — use cases + the ports (interfaces)
│       │   ├── ports/
│       │   │   ├── repositories.py   # CompanyRepository, DomainRepository, ... (interfaces)
│       │   │   ├── search.py         # SearchIndexPort
│       │   │   ├── fetcher.py        # PageFetcherPort
│       │   │   ├── queue.py          # QueuePort
│       │   │   └── unit_of_work.py   # transaction boundary
│       │   ├── dto/              #   SearchQuery, CompanySummaryDTO, ... (boundary data)
│       │   ├── use_cases/
│       │   │   ├── search/           # SearchCompanies, GetCompanyDetails
│       │   │   ├── discovery/        # DiscoverBusinesses
│       │   │   ├── enrichment/       # EnrichCompany, RunTechDetection, RunSeoScan, ...
│       │   │   └── scoring/          # RescoreCompany
│       │   └── errors.py             # application-level exceptions
│       │
│       ├── infrastructure/      # LAYER 3 — concrete implementations of ports
│       │   ├── db/
│       │   │   ├── models/            # SQLAlchemy ORM tables (persistence models)
│       │   │   ├── repositories/      # SQLAlchemy repository implementations
│       │   │   ├── unit_of_work.py    # SQLAlchemy UoW
│       │   │   └── migrations/        # Alembic versions
│       │   ├── search/
│       │   │   ├── postgres_fts.py    # v1 adapter (SearchIndexPort)
│       │   │   └── opensearch.py      # future adapter (same interface)
│       │   ├── crawling/
│       │   │   ├── httpx_fetcher.py   # PageFetcherPort impl
│       │   │   ├── playwright_fetcher.py
│       │   │   ├── robots.py          # robots.txt / crawl-delay compliance
│       │   │   └── sitemap.py
│       │   ├── analyzers/             # tech/seo/marketing/contact parsers (pure-ish libs)
│       │   │   ├── wappalyzer_rules.py
│       │   │   ├── seo_parser.py
│       │   │   ├── marketing_parser.py
│       │   │   └── contact_parser.py
│       │   ├── queue/
│       │   │   └── rq_queue.py        # QueuePort impl
│       │   └── cache/
│       │       └── redis_cache.py
│       │
│       ├── crawlers/            # worker-side orchestration of the 7 crawlers
│       │   ├── discovery_crawler.py
│       │   ├── website_crawler.py
│       │   ├── technology_crawler.py
│       │   ├── seo_crawler.py
│       │   ├── marketing_crawler.py
│       │   ├── location_crawler.py
│       │   └── classification_crawler.py
│       │
│       ├── presentation/       # LAYER 4 — entrypoints
│       │   ├── api/
│       │   │   ├── main.py            # FastAPI app factory
│       │   │   ├── routers/           # search, companies, crawlers, stats, settings, health
│       │   │   ├── schemas/           # pydantic request/response models (API-only)
│       │   │   ├── dependencies.py    # FastAPI DI → use cases
│       │   │   └── errors.py          # exception → HTTP status mapping
│       │   ├── workers/
│       │   │   ├── worker.py          # queue consumer bootstrap
│       │   │   └── handlers.py        # job name → use case dispatch
│       │   ├── scheduler/
│       │   │   └── scheduler.py       # APScheduler recurring jobs
│       │   └── cli/
│       │       └── manage.py          # ops commands (seed, reindex, migrate)
│       │
│       └── shared/             # cross-cutting, dependency-free helpers
│           ├── result.py             # Result/Either type for error handling
│           ├── pagination.py
│           └── ids.py                # id generation
│
├── frontend/                   # React + Vite + TypeScript SPA
│   ├── src/
│   │   ├── pages/                    # Dashboard, Search, Results, Company, Settings, Stats, CrawlerMonitor
│   │   ├── components/               # reusable UI atoms/molecules
│   │   ├── features/                 # feature-sliced modules (search, company, crawler)
│   │   ├── api/                      # typed client for the Search API
│   │   ├── hooks/
│   │   ├── store/                    # client state
│   │   └── types/
│   └── package.json
│
├── tests/
│   ├── unit/                        # domain + application (no I/O)
│   │   ├── domain/
│   │   └── application/
│   ├── integration/                 # infrastructure against real Postgres/Redis
│   ├── contract/                    # each port has a shared contract test suite
│   └── e2e/                         # API-level black-box tests
│
└── scripts/
    ├── seed_data.py
    └── load_wappalyzer_rules.py
```

## Why every folder exists

| Folder | Why it exists |
|--------|---------------|
| `docs/architecture/` | The design is a deliverable and must be versioned with the code. |
| `config/settings.py` | One typed, validated place for configuration (12-factor). |
| `config/logging.py` | Structured logging must be configured once, centrally. |
| `config/containers.py` | The **composition root** — the only place that knows concrete classes. |
| `src/bise/domain/` | The heart: pure business rules, framework-free, so they never rot. |
| `domain/entities` vs `value_objects` | DDD distinction: identity+lifecycle vs immutable value. |
| `domain/services` | Home for logic that belongs to no single entity (scoring/classification rules). |
| `domain/events` | Enables the async pipeline to be described in domain terms, not queue terms. |
| `application/ports/` | The Repository & Gateway **interfaces** — the seams for testing and swapping. |
| `application/dto/` | Stable data shapes at the boundary; decouples internals from callers. |
| `application/use_cases/` | One class per operation → Single Responsibility, easy to test. |
| `infrastructure/db/models` vs `repositories` | Separate persistence shape from the repository that maps it to domain entities. |
| `infrastructure/db/migrations` | Schema evolves safely and reproducibly (Alembic). |
| `infrastructure/search/` | Houses both FTS and OpenSearch adapters behind one port — the swap seam. |
| `infrastructure/crawling/` | Real network I/O isolated so the rest of the system is deterministic. |
| `infrastructure/analyzers/` | Parsing/fingerprinting kept separate from orchestration for reuse & testing. |
| `infrastructure/queue/` & `cache/` | Concrete Redis/RQ hidden behind ports. |
| `src/bise/crawlers/` | The seven crawlers as orchestrators; they *use* infrastructure, not define it. |
| `presentation/api/` | HTTP entrypoint; `schemas` are API-only and never leak inward. |
| `presentation/workers/` | Queue consumers — the async entrypoint sharing the same use cases. |
| `presentation/scheduler/` | Periodic triggers isolated from business logic. |
| `presentation/cli/` | Operators need scriptable actions without the API. |
| `shared/` | Tiny cross-cutting utilities with no dependencies, safe to import anywhere. |
| `frontend/` | The SPA; `features/` uses feature-slicing so pages stay thin. |
| `tests/unit` | Fast, no-I/O tests of domain+application — the bulk of the pyramid. |
| `tests/integration` | Verify real adapters against real Postgres/Redis. |
| `tests/contract` | One shared suite each port's implementations must pass → guarantees swap-safety. |
| `tests/e2e` | Black-box confidence at the API edge. |
| `scripts/` | Repeatable ops (seeding, loading rule sets) kept out of the app package. |

**Enforcement note:** an import-linter contract will assert the dependency rule
(`domain !-> application !-> infrastructure/presentation`) so violations fail CI, not review.
