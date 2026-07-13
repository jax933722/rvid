# Business Intelligence Search Engine — Architecture Dossier

> **Status:** Milestone 0 — System Architecture (design only, no application code)
> **Author:** Lead Software Architect
> **Scope target:** localhost for v1 → horizontally scalable to millions of indexed businesses

This dossier is the single source of truth for the system design. It is intentionally
technology-conservative: **only open-source tools, no paid APIs, no AI APIs, no LinkedIn.**

Every decision in these documents is justified against one constraint above all:

> **"Runs on a laptop today, scales to millions of businesses tomorrow — without a rewrite."**

## Deliverables Index

> **Start here:** [phase-1-design.md](./phase-1-design.md) is the authoritative
> reconciliation of the refined 10-module spec (Company Intelligence, Business
> Classification, SQLite+Postgres, saved searches/bookmarks/exports, concrete frontend
> stack). Docs 01–10 below provide the underlying depth it references.

| # | Document | Purpose |
|---|----------|---------|
| ★ | [phase-1-design.md](./phase-1-design.md) | Phase 1 deliverable: refined spec reconciled — modules, schema, ER, API, layout |
| 1 | [01-system-architecture.md](./01-system-architecture.md) | High-level component diagram (Mermaid) of the whole platform |
| 2 | [02-clean-architecture.md](./02-clean-architecture.md) | The four layers and their responsibilities |
| 3 | [03-folder-structure.md](./03-folder-structure.md) | Complete repository layout, every folder justified |
| 4 | [04-database-design.md](./04-database-design.md) | Normalized schema, relationships, ER diagrams |
| 5 | [05-search-engine-design.md](./05-search-engine-design.md) | Query model, filter composition, indexing, Elastic/OpenSearch path |
| 6 | [06-crawler-architecture.md](./06-crawler-architecture.md) | Seven specialized crawlers and their contracts |
| 7 | [07-api-architecture.md](./07-api-architecture.md) | Endpoint catalog, request/response shapes (design only) |
| 8 | [08-frontend-architecture.md](./08-frontend-architecture.md) | Page hierarchy and component design |
| 9 | [09-coding-standards.md](./09-coding-standards.md) | Naming, errors, logging, config, DI, testing |
| 10 | [10-roadmap.md](./10-roadmap.md) | ~50 session-sized milestones |
| 11 | [11-optimization-and-scale.md](./11-optimization-and-scale.md) | Phase 9: indexes added, text-search limitation, partitioning + adapter-swap scale path |

## Guiding Principles (applied throughout)

- **Clean Architecture** — dependencies point inward; the Domain knows nothing about the web, the DB, or the crawlers.
- **SOLID** — every module has one reason to change; abstractions over implementations.
- **Domain-Driven Design** — the language of "Company", "Domain", "Technology", "Score" is modeled explicitly.
- **Repository Pattern** — persistence is an interface the Domain owns and Infrastructure implements.
- **Reusability & Testability** — each module is independently importable and unit-testable behind a boundary.

## Recommended v1 Technology Stack (all open-source)

| Concern | v1 (localhost) | Scale path | Why |
|---------|----------------|------------|-----|
| Language | Python 3.11+ | same | Ecosystem for crawling + data |
| Web API | FastAPI | same | Async, typed, OpenAPI for free |
| ORM / DB access | SQLAlchemy 2.x + Alembic | same | Repository-friendly, migrations |
| Database | PostgreSQL 15 | Postgres + read replicas / Citus | JSONB, full-text, mature |
| Search | Postgres FTS (`tsvector`) + `pg_trgm` | Elasticsearch / OpenSearch | Zero new infra for v1 |
| Queue | Redis + RQ (or Postgres-backed) | RabbitMQ / Kafka | Simple locally, swappable |
| Scheduler | APScheduler | Celery beat / Temporal | In-process for v1 |
| Crawling | httpx + selectolax/BeautifulSoup + Playwright (JS pages) | distributed workers | Async, robots-aware |
| Tech detection | Wappalyzer fingerprint rules (open dataset) | same | No paid API |
| Frontend | React + Vite + TypeScript | same | SPA against Search API |
| Cache | Redis | Redis cluster | Hot query/result cache |
| Config | pydantic-settings + `.env` | Vault / env injection | 12-factor |
| Logging | structlog → JSON | ship to Loki/ELK | Structured from day one |
| Containers | Docker Compose | Kubernetes | Same images, new orchestrator |

Nothing above is load-bearing on a vendor. Every row's "v1" choice hides behind an
interface so the "scale path" is a configuration/adapter swap, not a rewrite.
