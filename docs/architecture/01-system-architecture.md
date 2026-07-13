# 1. High-Level System Architecture

The platform is a set of **independently deployable, independently testable modules**
that communicate through explicit contracts: HTTP for the UI↔API edge, a message
**Queue** for all long-running work, and the **Database** as the shared system of record.

The golden rule of the diagram: **nothing crawls or scores synchronously inside an HTTP
request.** The API only reads the database and enqueues jobs. All heavy work happens in
workers driven by the Queue and Scheduler.

## System Context (C4 Level 1)

```mermaid
flowchart LR
    User((Analyst / User))
    Admin((Operator))
    Web[Public Websites]

    subgraph Platform["Business Intelligence Search Engine"]
        FE[Frontend SPA]
        API[Search API / Backend]
        Workers[Crawler & Enrichment Workers]
        DB[(PostgreSQL)]
        SE[Search Engine Layer]
    end

    User -->|search, browse| FE
    Admin -->|monitor, configure| FE
    FE -->|HTTPS / JSON| API
    API --> SE
    API --> DB
    Workers --> DB
    Workers -->|HTTP fetch, robots-aware| Web
    SE --> DB
```

## Component Diagram (C4 Level 2 — the required components)

```mermaid
flowchart TB
    subgraph Presentation["Presentation"]
        FE["Frontend (React SPA)\nDashboard · Search · Results ·\nCompany · Settings · Stats · Crawler Monitor"]
    end

    subgraph Edge["Backend / API Edge"]
        SAPI["Search API\n(FastAPI routers)"]
        CFG["Configuration\n(pydantic-settings)"]
        LOG["Logging\n(structlog, JSON)"]
    end

    subgraph AppCore["Application Core (use cases)"]
        SEARCH["Search Engine\n(query builder + ranking)"]
        CLASS["Business Classification"]
        SCORE["Scoring Engine"]
    end

    subgraph Enrichment["Enrichment / Analysis Modules"]
        TECH["Technology Detection"]
        SEO["SEO Scanner"]
        MKT["Marketing Detection"]
        CONTACT["Contact Extraction"]
    end

    subgraph Ingestion["Ingestion"]
        DISC["Business Discovery Crawler"]
        WCRAWL["Website Crawler"]
        SCHED["Scheduler\n(APScheduler)"]
        QUEUE["Queue\n(Redis / RQ)"]
    end

    subgraph Data["Data / Persistence"]
        PG[("PostgreSQL\n(system of record)")]
        IDX["Search Index\n(FTS now → ES/OpenSearch later)"]
        CACHE[("Redis cache")]
    end

    FE -->|JSON| SAPI
    SAPI --> SEARCH
    SAPI --> CFG
    SAPI --> LOG
    SAPI --> CACHE
    SEARCH --> IDX
    SEARCH --> PG

    SCHED -->|enqueue recurring jobs| QUEUE
    SAPI -->|enqueue on-demand jobs| QUEUE
    QUEUE --> DISC
    QUEUE --> WCRAWL
    QUEUE --> TECH
    QUEUE --> SEO
    QUEUE --> MKT
    QUEUE --> CONTACT
    QUEUE --> CLASS
    QUEUE --> SCORE

    DISC --> PG
    WCRAWL --> PG
    TECH --> PG
    SEO --> PG
    MKT --> PG
    CONTACT --> PG
    CLASS --> PG
    SCORE --> PG
    PG --> IDX

    CFG -.->|reads settings| SAPI
    LOG -.->|structured logs| Data
```

## Data & Control Flow (end-to-end)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as Search API
    participant Q as Queue
    participant W as Workers
    participant DB as PostgreSQL
    participant IDX as Search Index

    Note over U,IDX: A) Discovery / enrichment pipeline (async)
    API->>Q: enqueue DiscoveryJob(seed/region)
    Q->>W: Business Discovery Crawler
    W->>DB: upsert Company + Domain (status=discovered)
    W->>Q: enqueue WebsiteCrawlJob(domain)
    Q->>W: Website Crawler fetches pages
    W->>DB: store raw pages / features
    W->>Q: fan-out: Tech, SEO, Marketing, Contact, Classify
    W->>DB: write Technologies, SEO, Marketing, Contacts
    W->>Q: enqueue ScoreJob(company)
    Q->>W: Scoring Engine
    W->>DB: write Scores
    DB->>IDX: index/refresh searchable projection

    Note over U,IDX: B) Search request (sync, read-only)
    U->>FE: enters query + filters
    FE->>API: GET /search?q=&filters=
    API->>IDX: build query, execute
    IDX-->>API: ranked company ids + facets
    API->>DB: hydrate company summaries
    API-->>FE: results + facets + pagination
```

## Component Responsibilities (one line each)

| Component | Single Responsibility |
|-----------|----------------------|
| **Frontend** | Render UI; call the Search API; never talk to the DB or queue directly. |
| **Backend / Search API** | Validate input, orchestrate use cases, read DB/index, enqueue jobs. |
| **Search Engine** | Translate filters → index query, rank, paginate, produce facets. |
| **Database** | Durable system of record; normalized truth for every entity. |
| **Business Discovery Crawler** | Find new businesses/domains from open sources → create Company/Domain rows. |
| **Website Crawler** | Fetch a domain's pages politely; produce raw HTML/features for analyzers. |
| **Technology Detection** | Fingerprint the stack (CMS, frameworks, analytics) from crawled pages. |
| **SEO Scanner** | Extract meta/robots/sitemap/structured-data signals and grade them. |
| **Business Classification** | Assign industry/category/size from signals (rule-based, no AI API). |
| **Marketing Detection** | Detect pixels, tag managers, ad/CRM/email tools. |
| **Contact Extraction** | Extract emails, phones, socials, addresses from pages. |
| **Queue** | Decouple request from work; buffer, retry, backpressure. |
| **Scheduler** | Trigger recurring/periodic jobs (recrawl, refresh, cleanup). |
| **Logging** | Structured, correlated logs across API and workers. |
| **Configuration** | One typed, validated source of settings per environment. |

## Why this shape scales

- **Queue in the middle** means workers scale horizontally without the API knowing.
- **DB as system of record + separate Search Index** lets us swap FTS→OpenSearch by
  changing one adapter (see doc 5) — business logic never learns which engine answered.
- **Every enrichment module is a queue consumer**, so tech/SEO/marketing/contact each
  scale, fail, retry, and deploy independently.
- **No synchronous crawling** keeps p99 API latency bounded regardless of crawl load.
