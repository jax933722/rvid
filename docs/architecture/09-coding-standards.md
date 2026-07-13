# 9. Coding Standards

These standards are **enforced in CI**, not left to reviewer memory. Tooling:
`ruff` (lint + format), `mypy --strict` (types), `pytest` (tests), `import-linter`
(dependency rule), `pre-commit` (gate before commit).

## Naming conventions

| Element | Convention | Example |
|---------|------------|---------|
| Packages / modules | `snake_case`, singular where it's a concept | `company_repository.py` |
| Classes | `PascalCase` | `SearchCompanies`, `PostgresFtsAdapter` |
| Functions / methods / vars | `snake_case` | `compile_query`, `page_size` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_PAGE_SIZE` |
| Interfaces (ports) | Noun + role, no `I` prefix | `CompanyRepository`, `SearchIndexPort` |
| Implementations | Tech-qualified | `SqlAlchemyCompanyRepository`, `RqQueueAdapter` |
| Use cases | Verb phrase | `DiscoverBusinesses`, `RescoreCompany` |
| DTOs | Noun + `DTO`/`Query`/`Command` | `CompanySummaryDTO`, `SearchQuery` |
| DB tables | plural `snake_case` | `company_technologies` |
| Test files | `test_<unit>.py` | `test_scoring_policy.py` |

Ubiquitous-language rule (DDD): the same word means the same thing in domain, DB, API, and
UI. "Company", "Domain", "Technology", "Score" are not renamed across layers.

## Error handling

- **Custom exception hierarchy per layer:** `DomainError` (invariant violations),
  `ApplicationError` (use-case failures, not-found, validation), and infrastructure errors
  wrapped — never let a raw `sqlalchemy`/`httpx` exception escape Infrastructure.
- **Expected outcomes use a `Result` type** (`shared/result.py`) rather than exceptions for
  control flow (e.g. "no results", "already exists"); exceptions are for the exceptional.
- **Presentation maps errors to transport:** one place (`api/errors.py`) turns
  `ApplicationError` → HTTP status + RFC7807 problem JSON with a `correlation_id`.
- **Crawlers never crash the worker:** a failed job is caught, recorded in `crawl_history`,
  and retried with backoff; poison jobs are dead-lettered, not silently dropped.
- **Fail loud in dev, degrade gracefully in prod** for non-critical enrichment.

## Logging

- **`structlog`, JSON output**, one event per line — greppable and shippable to Loki/ELK.
- **Correlation id** flows from the API request (or the originating job) through every log
  line and into `crawl_history`, so one pipeline run is fully traceable.
- **Levels:** `DEBUG` (dev detail), `INFO` (lifecycle: job started/finished), `WARNING`
  (recoverable/degraded), `ERROR` (failed operation), `CRITICAL` (system-level).
- **Never log secrets or full page bodies**; log identifiers, counts, durations, statuses.
- **No `print`** anywhere in `src/`.

## Configuration

- **`pydantic-settings`** class in `config/settings.py` is the single typed source; it
  validates on startup and fails fast on missing/invalid values.
- **12-factor:** config comes from environment; `.env` for local only, `.env.example`
  committed as documentation. **No secrets in the repo.**
- **No magic numbers in code** — crawl limits, page sizes, ranking weights, rate limits all
  live in settings so they're tunable without a deploy.
- **Per-environment** (`local`, `test`, `prod`) via env selection, same code.

## Testing

- **Pyramid:** many unit (domain + application, no I/O), fewer integration (real
  Postgres/Redis via Docker), few e2e (API black-box).
- **Contract tests per port:** one shared suite that *every* implementation of a port must
  pass (e.g. all `SearchIndexPort` adapters) — this is what makes FTS→OpenSearch swaps safe.
- **Fakes over mocks** for ports in unit tests (in-memory repositories) → readable,
  behavior-focused tests.
- **Fixtures, not the internet:** crawler logic is tested against recorded HTML/HTTP
  fixtures; CI never hits live sites.
- **Coverage gate** on `domain/` and `application/` (the parts that must not regress).
- **Deterministic:** inject `ClockPort` and id generators so time/ids are controllable.

## Dependency Injection

- **Constructor injection everywhere** — a use case receives its ports as constructor args;
  it never constructs its own dependencies.
- **One composition root** (`config/containers.py`) builds concrete objects and wires them.
  FastAPI's `Depends` and worker bootstrap pull fully-wired use cases from it.
- **No global singletons / service locators** inside business code — they hide dependencies
  and break testability.

## Repository Pattern

- **Interfaces live in `application/ports/repositories.py`** (owned by the inner layers).
- **Implementations live in `infrastructure/db/repositories/`** and map ORM models ⇄ domain
  entities — the domain entity is **not** the SQLAlchemy model.
- **Repositories expose domain-meaningful methods** (`find_by_domain`, `add`,
  `list_needing_enrichment`), never leak query builders or sessions.
- **Unit of Work** wraps multi-repository operations in one transaction.

## Environment variables

- Documented in `.env.example` with safe placeholder values and a comment each.
- Namespaced by concern: `DB_*`, `REDIS_*`, `SEARCH_BACKEND`, `CRAWL_*`, `LOG_*`.
- Read **only** through `settings.py` — no `os.getenv` scattered in code.
- Secrets injected at runtime (env / secret manager), never committed, never logged.

## General Python best practices

- Type hints on all public functions; `mypy --strict` green.
- Small functions, single responsibility; prefer pure functions in domain/application.
- `ruff format` is the only formatting authority (no debates).
- Docstrings explain **why**, not restate the code.
- Immutability by default for value objects (`frozen` dataclasses / pydantic models).
