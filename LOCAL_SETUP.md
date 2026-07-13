# Running BISE locally

This guide gets the **Business Intelligence Search Engine** running on your
computer — backend API + React frontend — using SQLite (no database server to
install). It takes ~5 minutes.

You do **not** need to copy files by hand: the complete project lives in the
GitHub repo. Clone it and follow the steps.

---

## 1. Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.11 or newer | `python3 --version` |
| Node.js | 18 or newer (22 recommended) | `node --version` |
| Git | any recent | `git --version` |

- **macOS**: `brew install python@3.11 node git`
- **Ubuntu/Debian**: `sudo apt install python3.11 python3.11-venv nodejs npm git`
- **Windows**: install Python from python.org and Node from nodejs.org (use
  **PowerShell** or **Git Bash**; the manual commands below work there).

> The backend requires Python **3.11+** (it uses `StrEnum` and modern typing).

---

## 2. Get the code

```bash
git clone https://github.com/jax933722/rvid.git
cd rvid
git checkout claude/bi-search-engine-architecture-hx2iy1
```

The project has two parts:

```
rvid/
├── src/bise/        backend (FastAPI + SQLAlchemy, Clean Architecture)
├── config/          settings, logging, DI composition root
├── frontend/        React + Vite + TypeScript + Tailwind SPA
├── scripts/         seed_demo.py (demo data)
└── tests/           157+ tests
```

---

## 3. Backend — install, migrate, seed

You can use the provided `Makefile` (macOS/Linux) **or** the manual commands
(any OS, incl. Windows).

### Option A — with Make (macOS/Linux)

```bash
make install      # creates .venv and installs the package + dev tools
make migrate      # creates bise.db (SQLite) and all tables
python scripts/seed_demo.py   # optional: 6 demo companies to explore
make serve        # starts the API at http://localhost:8000
```

### Option B — manual (any OS)

```bash
# from the repo root
python3 -m venv .venv

# activate the venv:
#   macOS/Linux:
source .venv/bin/activate
#   Windows PowerShell:
#   .venv\Scripts\Activate.ps1

pip install -U pip
pip install -e ".[dev]"

# create the database (SQLite file: bise.db)
alembic upgrade head

# optional: load 6 demo companies so the UI has content
python scripts/seed_demo.py

# run the API
uvicorn bise.presentation.api.main:app --reload
```

Backend is now at **http://localhost:8000**. Check it:

- Health: <http://localhost:8000/api/v1/health> → `{"status":"ok"}`
- **Interactive API docs (Swagger)**: <http://localhost:8000/docs>

> No `.env` is needed — it defaults to a local SQLite file `bise.db`.
> To customize, copy `.env.example` to `.env` and edit.

---

## 4. Frontend — install and run

Open a **second terminal** (leave the backend running):

```bash
cd rvid/frontend
npm install
npm run dev
```

Frontend is now at **http://localhost:5173** and it proxies `/api` to the
backend on port 8000 automatically. Open <http://localhost:5173> in your browser.

If you ran the seed script, you'll immediately see 6 companies on the Dashboard
and in Search. Try:
- **Search** page → filter by Industry "Dentistry", or click a Technology chip
  like "WordPress"; click a row to preview, then "Open full profile".
- **Crawler Monitor** → request a crawl / watch job status.
- Toggle **dark mode** (top-right).

---

## 5. Crawl a real website (optional)

The demo data is seeded directly. To crawl a live site end-to-end:

1. In the UI, create a company (or `POST /api/v1/companies` via <http://localhost:8000/docs>)
   with a domain, e.g. `example.com`.
2. **Crawler Monitor** → enter the hostname → **Request crawl** (creates a
   pending job).
3. Process the queued job with the worker:
   ```bash
   # from repo root, venv active
   python -c "from config.containers import Container; from bise.presentation.workers.crawl_worker import process_pending_jobs; print(process_pending_jobs(Container()))"
   ```
4. Then enrich + index the company (replace `1` with its id):
   ```bash
   curl -X POST http://localhost:8000/api/v1/companies/1/technologies/detect
   curl -X POST http://localhost:8000/api/v1/companies/1/marketing/detect
   curl -X POST http://localhost:8000/api/v1/companies/1/seo/scan
   curl -X POST http://localhost:8000/api/v1/companies/1/index
   ```
5. Refresh **Search** — the company now appears with its detected stack, SEO
   grade, and marketing tools.

> The crawler respects `robots.txt` and rate limits. Only crawl sites you're
> allowed to.

---

## 6. Run the tests (optional)

```bash
# backend (from repo root, venv active)
pytest                       # 157+ tests, all against in-memory SQLite
make check                   # lint + type-check + architecture rule + coverage gate

# frontend
cd frontend && npm run typecheck && npm run build
```

---

## 7. Reset / clean up

```bash
rm bise.db                   # delete the local database (re-run alembic + seed to recreate)
```

Stop the servers with `Ctrl+C` in each terminal.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python: command not found` | Use `python3`. On Windows, `py -3.11`. |
| Backend import errors on the seed script | Run it from the **repo root** with the venv active (it imports `config` and `bise`). |
| Frontend shows "Search failed / unreachable" | The backend isn't running on port 8000, or migrations weren't applied. |
| Port already in use | Change it: `uvicorn ... --port 8001` and update `frontend/vite.config.ts` proxy target, or `npm run dev -- --port 5174`. |
| `alembic: command not found` | Activate the venv, or use `python -m alembic upgrade head`. |
| Windows venv activation blocked | `Set-ExecutionPolicy -Scope Process RemoteSigned` then activate. |

---

## What runs where

| Service | URL | Command |
|---------|-----|---------|
| Backend API | http://localhost:8000 | `uvicorn bise.presentation.api.main:app --reload` |
| API docs (Swagger) | http://localhost:8000/docs | (served by the backend) |
| Frontend SPA | http://localhost:5173 | `npm run dev` (in `frontend/`) |

Everything is open-source and local — no paid APIs, no external services.
