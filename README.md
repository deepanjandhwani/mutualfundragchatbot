# IndMoney Mutual Fund RAG Chatbot

A **facts-only** RAG chatbot that answers factual queries about HDFC mutual funds listed on IndMoney. Uses **Playwright** for scraping and **ChromaDB** for embeddings.

## Key Constraints

- **Facts-only**: No investment advice; refuses opinionated questions
- **Privacy**: Never accepts/stores PAN, Aadhaar, account numbers, OTPs, emails, phone numbers
- **No computations**: Does not compute or compare returns; returns source URL when asked
- **Concise**: Answers ≤3 sentences with "Last updated from sources" and citation links

## Phase Structure

| Phase | Folder | Purpose |
|-------|--------|---------|
| 1 | `phase1_data_ingestion/` | Scrape 8 IndMoney fund URLs with Playwright |
| 2 | `phase2_processing/` | Parse, chunk, validate (no PII) |
| 3 | `phase3_embeddings/` | Embed chunks and store in ChromaDB |
| 4 | `phase4_backend/` | RAG API with safety checks |
| 5 | `phase5_frontend/` | Tiny chat UI (facts-only) |
| 6 | `phase6_scheduler/` | Scheduler to refresh data and trigger pipeline |

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed phase-wise architecture, data flow, and implementation order.

## Tech Stack

- **Scraping**: Playwright (Chromium)
- **Embeddings**: ChromaDB + sentence-transformers
- **Backend**: FastAPI
- **Frontend**: Vanilla HTML/CSS/JS

## Environment

Secrets are loaded from a `.env` file in the project root (do not commit it).

1. Copy the template: `cp .env.example .env`
2. Edit `.env` and set your keys, e.g.:
   - **GROQ_API_KEY** — Required for Phase 4 (RAG). Get a key at [Groq Console](https://console.groq.com/). Optional: **GROQ_MODEL** (default: `llama-3.3-70b-versatile`).

The backend (Phase 4) reads `GROQ_API_KEY` via `os.getenv` or `python-dotenv`. Keep `.env` in `.gitignore`.

## Getting Started

1. Create virtual environment: `python -m venv venv && source venv/bin/activate`
2. Install root deps: `pip install -r requirements.txt`
3. Install Playwright browsers: `playwright install chromium`
4. Add your keys to `.env` (see **Environment** above)
5. Implement phases in order: 1 → 2 → 3 → 4 → 5 → 6

### Running the frontend (Phase 5)

1. Start the backend (Phase 4): `python -m phase4_backend.run` (or `uvicorn phase4_backend.app:app --port 8000`).
2. Open `phase5_frontend/index.html` in a browser (e.g. via a local server to avoid CORS: `cd phase5_frontend && python -m http.server 3000` then open `http://localhost:3000`).
3. If the backend runs on another port, set `API_BASE_URL` in `phase5_frontend/config.js` (e.g. `http://127.0.0.1:8002`).
4. The UI shows **"Data last updated: &lt;date&gt;"** when the Phase 6 pipeline has been run; that date is when data was last fetched from the URLs.

### Running the scheduler (Phase 6)

Run the full refresh pipeline (Phase 1 → 2 → 3) and update the **last_updated** date shown in the frontend:

```bash
python -m phase6_scheduler.run
```

On success, `shared/last_refresh.json` is written; the backend serves it via **GET /meta** and the frontend displays it.

**GitHub Actions:** A workflow runs the scheduler **daily at 6 AM UTC** (see `.github/workflows/scheduler.yml`). You can also trigger it manually from the Actions tab. Artifacts (e.g. `last_refresh.json`, ChromaDB) are uploaded on success for use in deploy or backup.

## Deploy on Vercel

The project is set up to deploy **frontend and backend together** on Vercel.

1. **Connect the repo** to Vercel ([vercel.com/new](https://vercel.com/new)) and import this repository.
2. **Environment variables:** In the Vercel project, set **GROQ_API_KEY** (and optionally **GROQ_MODEL**). Do not commit these.
3. **Deploy:** Vercel will use `app.py` as the FastAPI entrypoint and run `buildCommand` to copy `phase5_frontend/` into `public/`. The site root serves the frontend; `/chat`, `/health`, and `/meta` are handled by the backend.
4. **Local vs production:** The frontend uses `http://127.0.0.1:8000` when opened from `localhost`; on your Vercel domain it uses the same origin (no `API_BASE_URL` needed).

**Limitations:** The serverless function includes ChromaDB and the embedding model. If the deployment exceeds Vercel’s bundle size limit (~500 MB), exclude more folders in `vercel.json` under `functions.app.py.excludeFiles`, or run the pipeline (Phase 1–3) and deploy with a pre-built `phase3_embeddings/chroma_db` and optional `shared/last_refresh.json` in the repo. The scheduler does not run on Vercel; use GitHub Actions (see above) and optionally wire artifacts into your deploy.
