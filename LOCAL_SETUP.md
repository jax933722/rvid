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
├── scripts/         seed_demo.py · enrichment_worker.py · lead_engine.py
└── tests/           312 tests
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

### Option B — manual, macOS/Linux

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
alembic upgrade head                 # creates bise.db
python scripts/seed_demo.py          # optional demo data
uvicorn bise.presentation.api.main:app --reload
```

### Option C — manual, Windows

Use `python` (NOT `python3` — on Windows `python3` opens the Microsoft Store).

**Command Prompt (cmd.exe):**
```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -e ".[dev]"
alembic upgrade head
python scripts\seed_demo.py
uvicorn bise.presentation.api.main:app --reload
```

**PowerShell** — same, but activate with:
```powershell
.\.venv\Scripts\Activate.ps1
# if blocked once: Set-ExecutionPolicy -Scope Process RemoteSigned
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

## 5. Keep leads coming — the Lead Engine (optional)

The **Lead Engine** turns discovery into a continuous flow of *net-new* leads.
A campaign describes your ideal customer as **business types × locations**; a
rotation cursor sweeps that grid one cell per run, and only businesses you've
never seen become leads.

1. In the UI, open **Lead Engine** (left nav) and create a campaign — e.g.
   business types `dentist, cafe`, locations `Sydney, Melbourne`. Tick
   **Auto-enrich** to queue each new lead for enrichment.
2. Click **Run now** on a campaign (or **Run all due**) to fire a cycle. New
   companies land in the **lead inbox** below, freshest first; download them as
   CSV anytime.
3. For hands-off operation, run the scheduler in its own terminal — it runs each
   due campaign on a loop against the same database:

   ```bash
   # from repo root, venv active
   python scripts/lead_engine.py             # run due campaigns forever
   python scripts/lead_engine.py --once      # run everything due once, then exit
   ```

> Discovery uses **OpenStreetMap** (Overpass/Nominatim) — free, no key. If a run
> finds nothing, try a broader location string (e.g. `Sydney, Australia`).

### Background enrichment worker (optional)

Enrichment (crawl → detect tech/marketing → SEO → people → index) runs as a
background job queue. Drain it in-app from the **Enrichment** UI, or run the
worker as a separate process:

```bash
python scripts/enrichment_worker.py          # drain the queue, then poll
python scripts/enrichment_worker.py --once    # drain once and exit
```

Both workers share the API's database (`BISE_DATABASE_URL`), so jobs and
campaigns created in the UI are picked up automatically.

---

## 6. Crawl a real website (optional)

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

## 7. Run the tests (optional)

```bash
# backend (from repo root, venv active)
pytest                       # 312 tests, all against in-memory SQLite
make check                   # lint + type-check + architecture rule + coverage gate

# frontend
cd frontend && npm run typecheck && npm run build
```

---

## 8. Reset / clean up

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
| Lead Engine scheduler | (background) | `python scripts/lead_engine.py` |
| Enrichment worker | (background) | `python scripts/enrichment_worker.py` |

Everything is open-source and local — no paid APIs, no external services.

---

## Optional configuration (`BISE_*` env vars)

No `.env` is needed for local use. To customize, copy `.env.example` to `.env`.
Highlights:

| Variable | Default | Purpose |
|---|---|---|
| `BISE_DATABASE_URL` | `sqlite:///./bise.db` | SQLite (dev) or PostgreSQL (prod) — one swap seam |
| `BISE_AUTH_ENABLED` | `false` | Require an API key (`Authorization: Bearer …`) when true |
| `BISE_RATE_LIMIT_ENABLED` / `_PER_MINUTE` / `_BURST` | `true` / `300` / `300` | Per-key/IP token bucket |
| `BISE_CACHE_ENABLED` / `_TTL_SECONDS` | `true` / `30` | Search response cache |

Auth is **off by default**, so local use needs no key; when you flip it on, mint
keys from **Settings → API keys** in the UI (the secret is shown once).
