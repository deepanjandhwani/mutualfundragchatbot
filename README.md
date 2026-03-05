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

1. Create virtual environment: `python3 -m venv venv && source venv/bin/activate` (or use `.venv` instead of `venv`)
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

## Deployment: Backend on Railway, Frontend on Vercel

**Why not Streamlit for the backend?** Streamlit hosts Streamlit apps (Python UIs), not REST APIs. The frontend is a static site that calls a backend API, so the backend is deployed as a web service (Railway) and the frontend as a static site (Vercel).

### Backend on Railway

**Railway free tier has a 5-minute build timeout.** The backend image (sentence-transformers + deps) often exceeds that, so builds can time out during “importing to docker”. Use the **pre-built image** (Option B) on the free tier, or upgrade to Hobby (20 min timeout) to build on Railway.

**Option B – Pre-built image (recommended on free tier; no timeout)**  
1. The workflow `.github/workflows/build-backend-image.yml` builds the backend image and pushes it to **GitHub Container Registry** (GHCR) on pushes to `main` that touch backend code. Run it once (push to `main` or trigger manually in the Actions tab).  
2. In [Railway](https://railway.app), create a **Web Service** → **Deploy from Docker image** (not “GitHub repo”). Image: `ghcr.io/<your-github-username>/mutualfundrag-backend:latest`.  
3. Make the GHCR package public (or add a token in Railway so it can pull). In Railway **Variables**, add **GROQ_API_KEY** (and optionally **GROQ_MODEL**).  
4. Deploys are pull + start only (no build on Railway, so no timeout). Re-run the workflow when you change backend code to refresh the image.

**Option A – Build on Railway (needs Hobby or Pro if build &gt; 5 min)**  
1. Push your repo to GitHub (include `phase3_embeddings/chroma_db/` and optionally `.cache/`).  
2. In Railway, create a project, connect the repo, add a **Web Service**. Railway will use the **Dockerfile**.  
3. Add **GROQ_API_KEY** in the service **Variables**.  
4. On the free tier the build may time out; on Hobby (20 min timeout) it should succeed.

### Frontend on Vercel

1. In [Vercel](https://vercel.com), import the same GitHub repository.
2. Add **API_BASE_URL** in Environment Variables and set it to your Railway backend URL (e.g. `https://your-app.up.railway.app`) with no trailing slash.
3. Deploy. The build runs `scripts/build-vercel.sh`, which injects `API_BASE_URL` and copies `phase5_frontend/` to `public/`. Set **Output Directory** to `public` if required.
4. The deployed site will serve the chat UI and call the Railway backend for `/chat`, `/meta`, and `/health`.

