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

Milestone 1 — repository scaffolding & tooling. See the
[roadmap](./docs/architecture/10-roadmap.md) for the milestone plan.
