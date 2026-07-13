# Business Intelligence Search Engine (BISE)

Discovers, crawls, enriches, and searches business websites — built to run on
localhost today and scale to millions of businesses without a rewrite.

Open-source only. No paid APIs, no AI APIs, no LinkedIn.

## Architecture

The full design of record lives in [`docs/architecture/`](./docs/architecture/README.md):
Clean Architecture, DDD, Repository Pattern, a normalized schema, seven crawlers,
and a ~50-milestone roadmap.

## Layout (Clean Architecture — dependencies point inward)

```
src/bise/
  domain/          # pure business rules (framework-free)
  application/     # use cases + ports (interfaces)
  infrastructure/  # concrete adapters (DB, search, crawling, queue)
  crawlers/        # worker-side crawler orchestrators
  presentation/    # API, workers, scheduler, CLI
  shared/          # cross-cutting helpers
config/            # settings, logging, composition root
tests/             # unit · integration · contract · e2e
```

## Development

```bash
make install    # create .venv and install package + dev tooling
make lint       # ruff
make typecheck  # mypy --strict
make arch       # Clean Architecture dependency rule (import-linter)
make test       # pytest
make check      # all quality gates (what CI runs)
```

Copy `.env.example` to `.env` for local configuration. Never commit secrets.

## Status

All build phases complete (design → backend → crawler → tech detection → SEO →
search → frontend → testing → optimization):

- **Backend**: FastAPI + SQLAlchemy, Clean Architecture across
  domain/application/infrastructure/presentation; SQLite (dev) / PostgreSQL
  (prod) behind one URL; 7 Alembic migrations (all reversible).
- **Pipeline**: discover → crawl (robots-aware) → detect technologies → SEO scan
  → build search projection, all fixture-tested with no live network in CI.
- **Search**: Sales-Navigator-style faceted search behind a swappable
  `SearchIndexPort` (portable SQL now; Postgres FTS / OpenSearch later).
- **Frontend**: React + Vite + TypeScript + Tailwind SPA (typecheck + build in CI).
- **Quality**: 157 tests, mypy `--strict`, import-linter enforcing the dependency
  rule, port contract suites, and a 90% coverage gate on domain + application.

Run the whole system locally: `make install && make migrate && make serve`
(backend) and `npm install && npm run dev` in [`frontend/`](./frontend).

See the [architecture dossier](./docs/architecture/README.md) and the
[roadmap](./docs/architecture/10-roadmap.md).

### Future modules (designed for, not yet built)

Marketing scanner, business classifier, location extractor, and company
intelligence each have a reserved port/table seam (see
[phase-1-design.md](./docs/architecture/phase-1-design.md)); email finder,
verification, auth, and multi-tenancy remain explicitly out of scope.
