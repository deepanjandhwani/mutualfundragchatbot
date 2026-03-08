# IndMoney Mutual Fund RAG Chatbot — Phase-wise Architecture

## Overview

This document describes the phase-wise architecture for a **facts-only** RAG chatbot that answers factual queries about HDFC mutual funds listed on IndMoney. The system uses **Playwright** for web scraping and **ChromaDB** for vector embeddings. Deployment is out of scope for this document.

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Facts-only** | No investment advice; refuse opinionated questions |
| **Privacy** | Never accept/store PII from **user input** (PAN, Aadhaar, account numbers, OTPs, emails, phone numbers); reject such queries. Scraped fund data is not PII-filtered when stored. |
| **No computations** | Do not compute/compare returns; return source URL when asked |
| **Concise answers** | ≤3 sentences per response |
| **Attribution** | Every answer: "Last updated from sources" + citation links |
| **Transparency** | UI clearly states facts-only, no advice |

---

## Environment Variables

Secrets are loaded from a **`.env`** file in the project root. Do not commit `.env`; use **`.env.example`** as a template.

| Variable | Used in | Description |
|----------|---------|--------------|
| **GEMINI_API_KEY** | Phase 4 (Backend) | API key for Google Gemini LLM. Get one at [Google AI Studio](https://aistudio.google.com/apikey). |

In Phase 4, read the key with `os.getenv("GEMINI_API_KEY")` (or load `.env` via `python-dotenv` before starting the app). Keep the key out of `config.py` and version control.

---

## Phase Structure

```
mutualfundragchatbot/
├── phase1_data_ingestion/      # Scrape & store raw data from 8 URLs
├── phase2_processing/          # Parse, structure, validate data
├── phase3_embeddings/          # Generate embeddings & store in ChromaDB
├── phase4_backend/             # RAG API, query handling, safety checks
├── phase5_frontend/            # Chat UI (tiny, facts-only)
├── phase6_scheduler/           # Cron/job to refresh data & trigger pipeline
└── shared/                     # Common config, schemas, constants
```

---

## Phase 1: Data Ingestion

**Folder:** `phase1_data_ingestion/`

**Purpose:** Fetch raw HTML/data from 8 IndMoney mutual fund URLs using Playwright.

### Source URLs

| # | Fund | URL |
|---|------|-----|
| 1 | HDFC Large Cap Fund | `https://www.indmoney.com/mutual-funds/hdfc-large-cap-fund-direct-plan-growth-option-2989` |
| 2 | HDFC Flexi Cap Fund | `https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184` |
| 3 | HDFC ELSS Tax Saver | `https://www.indmoney.com/mutual-funds/hdfc-elss-taxsaver-direct-plan-growth-option-2685` |
| 4 | HDFC Nifty Next 50 Index Fund | `https://www.indmoney.com/mutual-funds/hdfc-nifty-next-50-index-fund-direct-growth-1040010` |
| 5 | HDFC Mid Cap Fund | `https://www.indmoney.com/mutual-funds/hdfc-mid-cap-fund-direct-plan-growth-option-3097` |
| 6 | HDFC Housing Opportunities Fund | `https://www.indmoney.com/mutual-funds/hdfc-housing-opportunities-fund-direct-growth-9006` |
| 7 | HDFC Nifty LargeMidcap 250 Index Fund | `https://www.indmoney.com/mutual-funds/hdfc-nifty-largemidcap-250-index-fund-direct-growth-1047724` |
| 8 | HDFC Large and Mid Cap Fund | `https://www.indmoney.com/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth-2874` |

### Data Points to Extract (Factual Only)

| Category | Fields |
|----------|--------|
| **Overview** | NAV, AUM, Expense Ratio, Min Lumpsum/SIP, Lock-in, Risk, Benchmark, Inception Date, Exit Load, Turnover |
| **Performance** | 1Y returns, 3Y returns (stated values only; no computation) |
| **Engagement** | Number of people who invested in last 3 months |
| **Asset Allocation** | Fund asset allocation, asset allocation changes |
| **Sector Allocation** | Sector-wise breakdown |
| **Holdings** | Top holdings, portfolio changes |
| **About** | About section, Fund Manager details |
| **FAQ** | FAQ section of fund pages |

### Components

```
phase1_data_ingestion/
├── config.py              # URL list, selectors, timeouts
├── scraper.py             # Playwright-based scraper
├── run.py                 # Entry point to run ingestion
├── output/                # Raw HTML/JSON per fund (versioned by timestamp)
│   └── {fund_id}_{timestamp}.json
└── requirements.txt       # playwright, etc.
```

### Scraper Behavior

- Use **Playwright** (Chromium) for JS-rendered pages
- Respect `robots.txt` and reasonable rate limits
- Save raw content (HTML or extracted JSON) with timestamp
- Handle timeouts and retries
- Log success/failure per URL

### Output Schema (Raw)

```json
{
  "fund_id": "2989",
  "fund_name": "HDFC Large Cap Fund Direct Plan Growth",
  "url": "https://www.indmoney.com/mutual-funds/...",
  "scraped_at": "2025-03-04T10:00:00Z",
  "raw_html": "...",
  "extracted_sections": {
    "overview": "...",
    "performance": "...",
    "asset_allocation": "...",
    "holdings": "...",
    "faq": "..."
  }
}
```

---

## Phase 2: Processing

**Folder:** `phase2_processing/`

**Purpose:** Parse raw data into structured chunks suitable for RAG.

### Components

```
phase2_processing/
├── config.py
├── parsers/
│   ├── overview_parser.py
│   ├── performance_parser.py
│   ├── allocation_parser.py
│   ├── holdings_parser.py
│   └── faq_parser.py
├── chunker.py             # Split into semantic chunks (e.g., by section)
├── validator.py           # PII helpers for Phase 4 (not used when loading data)
├── run.py                 # Read phase1 output → write structured chunks
├── input/                 # Symlink or copy from phase1/output
└── output/
    └── chunks/
        └── {fund_id}_{chunk_id}.json
```

### Chunk Schema

```json
{
  "chunk_id": "2989_overview_1",
  "fund_id": "2989",
  "fund_name": "HDFC Large Cap Fund",
  "section": "overview",
  "content": "NAV: ₹X.XX. AUM: ₹X,XXX Cr. Expense Ratio: X.XX%. Min SIP: ₹500. Lock-in: None. Risk: Moderately High. Benchmark: Nifty 50. Inception: DD-MM-YYYY. Exit Load: X%. Turnover: X%.",
  "source_url": "https://www.indmoney.com/mutual-funds/...",
  "last_updated": "2025-03-04"
}
```

### PII and data loading

- **PII filtering is not applied when loading or storing scraped data.** Phase 2 keeps all parsed chunks (overview, performance, NAV, etc.); scraped content is treated as factual fund information.
- PII checks apply **only to user input** at query time (see Phase 4).

---

## Phase 3: Embeddings & ChromaDB

**Folder:** `phase3_embeddings/`

**Purpose:** Generate embeddings for chunks and store in ChromaDB.

### Components

```
phase3_embeddings/
├── config.py              # ChromaDB path, embedding model
├── embedder.py            # Load model, generate embeddings
├── chroma_client.py       # ChromaDB collection setup, upsert, query
├── run.py                 # Read chunks → embed → store
├── chroma_db/             # ChromaDB persistent storage
└── requirements.txt       # chromadb, sentence-transformers or openai
```

### ChromaDB Collection

- **Collection name:** `indmoney_fund_chunks`
- **Metadata:** `fund_id`, `fund_name`, `section`, `source_url`, `last_updated`
- **Embedding model:** e.g., `all-MiniLM-L6-v2` or `BAAI/bge-small-en-v1.5` (configurable)

### Behavior

- Upsert chunks; use `chunk_id` or composite key for idempotency
- On full refresh: clear collection and re-insert
- Support metadata filtering (e.g., by `fund_id`, `section`)

### Deployment (embedding model)

- **Local cache:** The sentence-transformers model is stored under `.cache/huggingface/` (in repo root). This directory is **gitignored** so it is not committed. Locally, after the first run (or a one-time download), the model is loaded from cache and no network call is needed.
- **At deploy:** On a fresh server or container, `.cache/` will not exist. The embedder will then try to download from Hugging Face once. If the environment has no outbound access (e.g. locked-down network), the download will fail.
- **Recommended for production:** Either (1) **bake the model into the image**: copy `.cache/huggingface/` (or the snapshot folder) into the container at build time, or (2) set **`EMBEDDING_CACHE_DIR`** to a path where the model is already present (e.g. a mounted volume or a path in the image). The embedder uses this env var when set, so no Hugging Face connection is required at runtime.

---

## Phase 4: Backend (RAG API)

**Folder:** `phase4_backend/`

**Purpose:** Serve RAG API with query handling, safety checks, and response formatting. The **system prompt** is defined and applied here. **Google Gemini** is used as the LLM for generating answers from retrieved context.

### LLM: Google Gemini

- **Provider:** [Google Gemini](https://ai.google.dev/) via `google-generativeai` SDK
- **Model:** `gemini-2.5-flash-lite` (default, configurable via `GEMINI_MODEL` env var)
- **Free-tier limits:** 1,000 requests/day, 250K tokens/minute, no daily token cap
- **Usage:** In Phase 4, retrieved chunks + user query + system prompt are sent to Gemini to generate the factual answer (≤3 sentences, with attribution).
- **Config:** Model name in `phase4_backend/config.py`. API key from **environment** (see Environment Variables).

### Components

```
phase4_backend/
├── config.py
├── app.py                 # FastAPI/Flask app
├── rag/
│   ├── retriever.py       # ChromaDB retrieval + fund name alias expansion
│   ├── prompt_builder.py  # System prompt + user prompts (facts-only)
│   └── response_formatter.py
├── safety/
│   ├── input_validator.py # Block PII in user message, opinionated queries
│   └── query_classifier.py # Detect "should I buy/sell", comparison requests
├── routes/
│   ├── chat.py            # POST /chat (accepts optional fund_ids filter)
│   └── meta.py            # GET /meta, GET /funds
├── run.py
└── requirements.txt
```

### System Prompt (Written in Phase 4)

The system prompt is implemented in `rag/prompt_builder.py`. It instructs the LLM to:

- Answer **factual queries only** (NAV, AUM, expense ratio, returns, allocation, holdings, overview, FAQ, etc.)
- When **multiple funds** are in context, answer for **all** of them (one sentence per fund); otherwise ≤3 sentences
- Always include **"Last updated from sources"** and cite source URLs
- **Do not** give investment advice or recommendations
- **Do not** compute or compare returns
- Refuse opinionated or comparison-style questions with a polite, facts-only message and relevant educational link

### API Contract

**POST /chat**

```json
// Request (fund_ids is optional; omit or null for all funds)
{
  "message": "What is the NAV of HDFC Large Cap Fund?",
  "fund_ids": ["2989", "3184"]
}

// Response
{
  "answer": "The NAV of HDFC Large Cap Fund Direct Plan Growth is ₹XX.XX as of [date]. Last updated from sources.",
  "sources": [
    {
      "url": "https://www.indmoney.com/mutual-funds/hdfc-large-cap-fund-direct-plan-growth-option-2989",
      "label": "HDFC Large Cap Fund - IndMoney"
    }
  ],
  "refused": false,
  "refusal_reason": null
}
```

### Fund Name Alias Expansion

Before embedding the query for ChromaDB search, the retriever expands short/partial fund names to their full canonical names. This ensures queries like "HDFC ELSS" or "midcap" retrieve the correct chunks.

| Short query contains | Expands to |
|---------------------|------------|
| "elss", "tax saver" | HDFC ELSS TaxSaver Fund |
| "flexi cap", "flexicap" | HDFC Flexi Cap Fund |
| "large cap", "largecap" | HDFC Large Cap Fund |
| "mid cap", "midcap" | HDFC Mid Cap Fund |
| "next 50" | HDFC Nifty Next 50 Index Fund |
| "largemidcap", "largemidcap 250" | HDFC Nifty LargeMidcap 250 Index Fund |
| "large and mid cap" | HDFC Large and Mid Cap Fund |
| "housing" | HDFC Housing Opportunities Fund |

### Safety Logic

| Query Type | Action |
|------------|--------|
| **User message** contains PII (PAN, Aadhaar, account numbers, OTPs, email, phone) | Reject with "We don't accept or store personal identifiers." |
| "Should I buy/sell?" / opinionated | Refuse with polite message + educational link |
| "Compare returns" / compute returns | Refuse: "We don't compute or compare returns. Please check the source." + URL |
| Factual (NAV, AUM, etc.) | Process via RAG |

PII validation is applied **only to the user's chat input**, not to stored/scraped fund content.

### Fund Filtering (Multi-select)

The `/chat` endpoint accepts an optional `fund_ids` array. When provided, ChromaDB retrieval is filtered to only those funds using a `$in` metadata filter on `fund_id`. This allows users to select specific funds from the UI and ask generic questions like "What is the expense ratio?" without needing to include the fund name in the query.

A **GET /funds** endpoint returns the list of available funds (`id` + `name`) for the frontend to populate the filter dynamically.

### Response Rules

- When a single fund is in context: answer in ≤3 sentences
- When multiple funds are in context: answer for **all** funds (one sentence per fund); `max_output_tokens` scales dynamically
- Always append: "Last updated from sources."
- Include `sources` array with citation URLs
- No advice, no recommendations

---

## Phase 5: Frontend (Chat UI)

**Folder:** `phase5_frontend/`

**Purpose:** Minimal chat UI for facts-only queries.

### Components

```
phase5_frontend/
├── index.html
├── styles.css
├── app.js                 # Chat logic, API calls, fund filter, theme toggle
├── assets/
│   ├── indmoney-logo-dark.svg   # IndMoney logo for dark mode
│   └── indmoney-logo-light.svg  # IndMoney logo for light mode
└── config.js              # API base URL
```

### UI Layout

```
┌──────────────────────────────────────────────────────┐
│  [INDmoney logo]  Mutual Fund Facts    [🌙/☀ toggle] │
├──────────┬───────────────────────────────────────────┤
│ Filter   │  AI disclaimer banner                     │
│ by fund  │  Example questions (3 buttons)            │
│ ☑ All    │                                           │
│ ☑ Large  │  [Chat messages with citation links]      │
│ ☑ Flexi  │                                           │
│ ☑ ELSS   │  [Input box]                     [Send]   │
│ ...      │                                           │
│          │  How it works (footer)                     │
└──────────┴───────────────────────────────────────────┘
```

### Features

- **IndMoney logo** in header (auto-switches dark/light variant)
- **Dark/light mode toggle** — persists preference in localStorage
- **Fund filter** (sidebar) — multi-select checkboxes with "All Funds" toggle; populated dynamically from `GET /funds`; sends `fund_ids` with each query for targeted retrieval
- **"How it works"** — footer section below chat area
- 3 example query buttons
- AI disclaimer banner
- Citation links on every answer
- Rate limit and refusal styling

---

## Phase 6: Scheduler

**Folder:** `phase6_scheduler/`

**Purpose:** Periodically refresh data and run the full pipeline so the chatbot has the latest data.

### Components

```
phase6_scheduler/
├── config.py              # Cron schedule, phase paths
├── pipeline.py            # Orchestrate: phase1 → phase2 → phase3
├── run.py                 # Single run or cron entry point
└── requirements.txt
```

### Pipeline Flow

```
Phase 6 Scheduler (e.g., daily 6 AM)
    │
    ├─► Phase 1: Scrape 8 URLs → save raw data
    │
    ├─► Phase 2: Parse → chunks
    │
    ├─► Phase 3: Embed → ChromaDB (replace/upsert)
    │
    └─► Write shared/last_refresh.json (last_updated date for frontend)
    └─► (Phase 4 & 5 already running; new data available on next query)
```

After each successful pipeline run, Phase 6 writes **`shared/last_refresh.json`** with `last_updated` (date) and `updated_at_iso` (ISO timestamp). The backend exposes **GET /meta** returning this data; the frontend displays "Data last updated: &lt;date&gt;" so users see when the data was last fetched from the URLs.

### Scheduling Options

- **GitHub Actions:** Daily run at 6 AM IST (00:30 UTC) via `.github/workflows/scheduler.yml` (schedule + optional manual `workflow_dispatch`). Installs deps + Playwright Chromium, runs `python -m phase6_scheduler.run`, commits updated ChromaDB + `last_refresh.json` back to repo, and triggers the backend Docker image rebuild workflow.
- **Cron:** `0 6 * * *` (daily 6 AM) on a server
- **APScheduler:** In-process scheduler
- **External:** Systemd timer, Kubernetes CronJob (when deployment is added)

---

## Shared Module

**Folder:** `shared/`

```
shared/
├── __init__.py
├── config.py              # URLs, paths, constants
├── schemas.py             # Pydantic/dataclass models
├── constants.py           # PII patterns, refusal messages, educational URLs
└── utils.py               # Logging, date formatting
```

### Constants (Examples)

PII patterns are used **only when validating user chat input** (Phase 4), not when loading or storing scraped data.

```python
# PII patterns to block in user messages
PII_PATTERNS = [
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",  # PAN
    r"\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b",  # Aadhaar
    # ...
]

# Educational link for refused queries
EDUCATIONAL_LINK = "https://www.sebi.gov.in/..."

# Refusal messages
REFUSAL_OPINION = "We only provide factual information. For investment decisions, please consult a SEBI-registered advisor."
REFUSAL_COMPARE = "We don't compute or compare returns. Please check the fund page directly."
```

---

## Deployment

| Component | Platform | Details |
|-----------|----------|---------|
| **Frontend** | [Vercel](https://vercel.com/) | Static HTML/CSS/JS served from `phase5_frontend/`. Auto-deploys on push to `main`. `API_BASE_URL` in `config.js` points to the Railway backend. |
| **Backend** | [Railway](https://railway.app/) | Docker image from GHCR (`ghcr.io/<github-username>/mutualfundrag-backend:latest`). Environment variable `GEMINI_API_KEY` set in Railway dashboard. |
| **Docker image** | [GHCR](https://ghcr.io/) | Built by `.github/workflows/build-backend-image.yml` on every push to `main`. After build, triggers Railway redeploy via GraphQL API. |
| **CI/CD** | GitHub Actions | `scheduler.yml` runs daily data refresh → commits updated data → triggers `build-backend-image.yml` → GHCR push → Railway auto-redeploy. Fully automated. |

### GitHub Secrets Required

| Secret | Purpose |
|--------|---------|
| `RAILWAY_API_TOKEN` | Triggers Railway redeploy after image build |
| `RAILWAY_SERVICE_ID` | Identifies the Railway service to redeploy |
| `RAILWAY_ENVIRONMENT_ID` | Identifies the Railway environment |

---

## Technology Stack Summary

| Component | Technology |
|-----------|------------|
| Scraping | Playwright (Chromium) |
| Embeddings | ChromaDB + sentence-transformers (`all-MiniLM-L6-v2`) |
| **LLM (generation)** | **Google Gemini** (`gemini-2.5-flash-lite`) |
| Backend | FastAPI |
| Frontend | Vanilla HTML/CSS/JS |
| Scheduler | GitHub Actions (daily cron) |
| Deployment | Vercel (frontend) + Railway (backend via GHCR Docker image) |
| Python | 3.10+ |

---

## Data Flow Diagram

```
                    ┌──────────────────┐
                    │  Phase 6         │
                    │  Scheduler       │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  Phase 1       │  │  Phase 2       │  │  Phase 3       │
│  Data          │─►│  Processing    │─►│  Embeddings    │
│  Ingestion     │  │  (Parse/Chunk) │  │  (ChromaDB)    │
└────────────────┘  └────────────────┘  └────────┬───────┘
         │                   │                   │
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Phase 4         │
                    │  Backend API     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Phase 5         │
                    │  Frontend UI     │
                    └──────────────────┘
```

---

## Implementation Order

1. **Phase 1** — Playwright scraper for 8 URLs
2. **Phase 2** — Parsers + chunker (no PII filter on data; PII applies at query time in Phase 4)
3. **Phase 3** — ChromaDB setup + embedder
4. **Phase 4** — Backend API + system prompt + safety layer
5. **Phase 5** — Frontend UI
6. **Phase 6** — Scheduler + pipeline orchestration

---

## File Structure (Complete)

```
mutualfundragchatbot/
├── ARCHITECTURE.md
├── README.md
├── requirements.txt
├── shared/
│   ├── __init__.py
│   ├── config.py
│   ├── schemas.py
│   ├── constants.py
│   └── utils.py
├── phase1_data_ingestion/
│   ├── config.py
│   ├── scraper.py
│   ├── run.py
│   ├── output/
│   └── requirements.txt
├── phase2_processing/
│   ├── config.py
│   ├── parsers/
│   ├── chunker.py
│   ├── validator.py
│   ├── run.py
│   ├── input/
│   └── output/
├── phase3_embeddings/
│   ├── config.py
│   ├── embedder.py
│   ├── chroma_client.py
│   ├── run.py
│   ├── chroma_db/
│   └── requirements.txt
├── phase4_backend/
│   ├── config.py
│   ├── app.py
│   ├── rag/
│   ├── safety/
│   ├── routes/
│   ├── run.py
│   └── requirements.txt
├── phase5_frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── config.js
│   └── assets/
├── phase6_scheduler/
│   ├── config.py
│   ├── pipeline.py
│   ├── run.py
│   └── requirements.txt
```

---

## Next Steps (Post-Architecture)

1. Implement Phase 1 scraper and validate extraction from one URL
2. Define exact CSS/XPath selectors per IndMoney page structure
3. Implement Phase 2 parsers based on actual HTML structure
4. Set up ChromaDB and tune chunk size/overlap
5. Implement Phase 4 with system prompt and safety checks; test edge cases
6. Build Phase 5 UI and integrate with API
7. Add Phase 6 scheduler and test end-to-end pipeline
