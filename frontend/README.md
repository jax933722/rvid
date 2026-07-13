# BISE Frontend

React + Vite + TypeScript + Tailwind SPA for the Business Intelligence Search
Engine. A pure consumer of the backend Search API — no business logic lives here.

## Stack

- React 18 + Vite + TypeScript (strict)
- Tailwind CSS (dark mode via `class`)
- TanStack Query (server state) + TanStack Table (results grid)
- React Router

## Development

```bash
npm install
npm run dev        # http://localhost:5173  (proxies /api -> http://localhost:8000)
npm run typecheck  # tsc --noEmit
npm run build      # type-check + production build
```

Run the backend separately (`make serve` in the repo root) so the dev proxy can
reach `/api/v1`.

## Layout

```
src/
  api/         typed client + wire types (single source of the API contract)
  components/  Layout + reusable UI primitives
  features/    feature-sliced modules (search: filters, results table, preview)
  hooks/       cross-cutting hooks (theme)
  lib/         query client
  pages/       route shells: Dashboard, Search, Company, Crawler Monitor, Settings
```

## Pages

- **Dashboard** — KPI tiles and getting-started guidance.
- **Search** — Sales-Navigator 3-pane workspace: filters | results (TanStack
  Table) | company preview. Filters combine as OR within a field, AND across.
- **Company Details** — overview, detected technologies, and SEO tabs; rebuild
  the search index for the company.
- **Crawler Monitor** — request crawls and watch job status (auto-refreshing).
- **Settings** — theme, backend health, and crawler-config notes.
