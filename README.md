# IndMoney Mutual Fund RAG Chatbot

A **facts-only** RAG chatbot that answers factual queries about HDFC mutual funds listed on IndMoney. Uses **Playwright** for scraping and **ChromaDB** for embeddings.

## Key Constraints

- **Facts-only**: No investment advice; refuses opinionated questions
- **Privacy**: Never accepts/stores PAN, Aadhaar, account numbers, OTPs, emails, phone numbers
- **No computations**: Does not compute or compare returns; returns source URL when asked
- **Concise**: Single-fund answers ≤3 sentences; multi-fund answers use one sentence per fund. Always ends with "Last updated from sources" and citation links

## Phase Structure

| Phase | Folder | Purpose |
|-------|--------|---------|
| 1 | `phase1_data_ingestion/` | Scrape 8 IndMoney fund URLs with Playwright |
| 2 | `phase2_processing/` | Parse, chunk, validate (no PII) |
| 3 | `phase3_embeddings/` | Embed chunks and store in ChromaDB |
| 4 | `phase4_backend/` | RAG API with safety checks, per-fund retrieval, fund alias expansion |
| 5 | `phase5_frontend/` | Chat UI with fund filter, dark/light theme, IndMoney branding |
| 6 | `phase6_scheduler/` | Scheduler to refresh data and trigger pipeline |

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed phase-wise architecture, data flow, and implementation order.

## Tech Stack

- **Scraping**: Playwright (Chromium)
- **Embeddings**: ChromaDB + sentence-transformers (`all-MiniLM-L6-v2`)
- **LLM**: Google Gemini (`gemini-2.5-flash-lite`)
- **Backend**: FastAPI
- **Frontend**: Vanilla HTML/CSS/JS
- **Deployment**: Vercel (frontend) + Railway (backend Docker)

## Features

- **Fund filter (no cap)** — sidebar checkboxes; select one or more funds; queries are scoped via per-fund ChromaDB retrieval
- **Mention-based scoping** — if the question mentions specific fund(s), the answer is for those funds (even if different from filter); otherwise selected funds are used; if neither, all funds are used
- **Per-fund retrieval** — ChromaDB is queried separately per fund so each fund is represented in results
- **Fund alias expansion** — short names like "ELSS" or "Flexi Cap" are expanded to full canonical names before retrieval
- **Latency guardrails** — backend preloads embedding/Chroma on startup, applies Gemini timeout, and reduces effective `top_k` for 2/3-fund queries
- **Dark/light theme** — toggle in header, preference persisted in localStorage; IndMoney logo auto-switches variant
- **Thinking indicator** — pulsing timer shows elapsed seconds while waiting for a response
- **New Chat button** — clears the chat display
- **Mobile-first UX** — compact mobile header, sticky composer, larger touch targets/typography, and a bottom-sheet fund selector with backdrop + "Done"
- **No-fund availability message** — if no funds are configured at all, the chatbot shows a clear “no funds available” message instead of failing silently
- **Stateless** — each query is independent; no conversation memory
- **Dynamic response scaling** — multi-fund queries get one sentence per fund with scaled token limits; single-fund queries get ≤3 sentences

## Data Sources

The chatbot scrapes and indexes the following 8 HDFC mutual fund pages from IndMoney:

| # | Fund | URL |
|---|------|-----|
| 1 | HDFC Large Cap Fund | [indmoney.com/...hdfc-large-cap-fund...](https://www.indmoney.com/mutual-funds/hdfc-large-cap-fund-direct-plan-growth-option-2989) |
| 2 | HDFC Flexi Cap Fund | [indmoney.com/...hdfc-flexi-cap-fund...](https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184) |
| 3 | HDFC ELSS Tax Saver | [indmoney.com/...hdfc-elss-taxsaver...](https://www.indmoney.com/mutual-funds/hdfc-elss-taxsaver-direct-plan-growth-option-2685) |
| 4 | HDFC Nifty Next 50 Index Fund | [indmoney.com/...hdfc-nifty-next-50...](https://www.indmoney.com/mutual-funds/hdfc-nifty-next-50-index-fund-direct-growth-1040010) |
| 5 | HDFC Mid Cap Fund | [indmoney.com/...hdfc-mid-cap-fund...](https://www.indmoney.com/mutual-funds/hdfc-mid-cap-fund-direct-plan-growth-option-3097) |
| 6 | HDFC Housing Opportunities Fund | [indmoney.com/...hdfc-housing-opportunities...](https://www.indmoney.com/mutual-funds/hdfc-housing-opportunities-fund-direct-growth-9006) |
| 7 | HDFC Nifty LargeMidcap 250 Index Fund | [indmoney.com/...hdfc-nifty-largemidcap-250...](https://www.indmoney.com/mutual-funds/hdfc-nifty-largemidcap-250-index-fund-direct-growth-1047724) |
| 8 | HDFC Large and Mid Cap Fund | [indmoney.com/...hdfc-large-and-mid-cap...](https://www.indmoney.com/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth-2874) |

Data is refreshed daily at 6 AM IST via GitHub Actions (see Phase 6).

## Sample Q&A

Below are real responses from the chatbot (with HDFC Large Cap Fund selected in the filter):

**Q: What is the NAV of HDFC Large Cap?**
> The NAV of the HDFC Large Cap Fund today is ₹1235.91. Last updated from sources.
>
> *Sources: [HDFC Large Cap Fund Direct Plan Growth - IndMoney](https://www.indmoney.com/mutual-funds/hdfc-large-cap-fund-direct-plan-growth-option-2989)*

**Q: AUM of HDFC Large Cap Fund?**
> The AUM of the HDFC Large Cap Fund is ₹39,621 Cr. As of Jan'26, the AUM was ₹39.6K Cr. The AUM decreased by ₹983.4 Cr between Jan'26 and Dec'25. Last updated from sources.
>
> *Sources: [HDFC Large Cap Fund Direct Plan Growth - IndMoney](https://www.indmoney.com/mutual-funds/hdfc-large-cap-fund-direct-plan-growth-option-2989)*

**Q: Which sectors does this fund invest in?**
> The fund has significant allocations in the financial sector (34.35%), cyclical sectors (12.26%), and technology (9.80%). Other sectors include health (9.1%), industrial (7.9%), communication (6.2%), consumer defensive (6.2%), energy (5.7%), basic materials (5.4%), tech (4.9%), utilities (4.2%), and real estate (0.5%). Last updated from sources.
>
> *Sources: [HDFC Large Cap Fund Direct Plan Growth - IndMoney](https://www.indmoney.com/mutual-funds/hdfc-large-cap-fund-direct-plan-growth-option-2989)*

## Environment

Secrets are loaded from a `.env` file in the project root (do not commit it).

1. Copy the template: `cp .env.example .env`
2. Edit `.env` and set your keys, e.g.:
   - **GEMINI_API_KEY** — Required for Phase 4 (RAG). Get a key at [Google AI Studio](https://aistudio.google.com/apikey). Optional: **GEMINI_MODEL** (default: `gemini-2.5-flash-lite`).
   - Optional latency overrides: **GEMINI_TIMEOUT_SECONDS** (default `10`), **TOP_K_WHEN_2_FUNDS** (default `12`), **TOP_K_WHEN_3_FUNDS** (default `9`).

The backend (Phase 4) reads `GEMINI_API_KEY` via `os.getenv` or `python-dotenv`. Keep `.env` in `.gitignore`.

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
5. On mobile, use **Select funds (x/3)** to open the fund filter bottom sheet and close it with **Done**.

### Running the scheduler (Phase 6)

Run the full refresh pipeline (Phase 1 → 2 → 3) and update the **last_updated** date shown in the frontend:

```bash
python -m phase6_scheduler.run
```

On success, `shared/last_refresh.json` is written; the backend serves it via **GET /meta** and the frontend displays it.

**GitHub Actions:** A workflow runs the scheduler **daily at 6 AM IST (00:30 UTC)** (see `.github/workflows/scheduler.yml`). You can also trigger it manually from the Actions tab. On success, updated ChromaDB and `last_refresh.json` are committed back to the repo, and the backend Docker image rebuild is triggered automatically.

## Deployment: Backend on Railway, Frontend on Vercel

**Why not Streamlit for the backend?** Streamlit hosts Streamlit apps (Python UIs), not REST APIs. The frontend is a static site that calls a backend API, so the backend is deployed as a web service ([Railway](https://railway.app)) and the frontend as a static site ([Vercel](https://vercel.com)).

### Backend on Railway

1. Push this repo to GitHub (include `phase3_embeddings/chroma_db/` and `.cache/` so the Docker image has Chroma data and the Hugging Face model).
2. In [Railway](https://railway.app), create a **New Project** → **Deploy from GitHub repo** → select this repository, or **Empty project** → **New** → **GitHub Repo**.
3. Railway should detect the **`Dockerfile`** at the repo root. Set **Root Directory** to `/` if asked. Add a **public HTTP** port (Railway sets **`PORT`**; the image uses it automatically).
4. In **Variables**, add **`GEMINI_API_KEY`** (and optionally **`GEMINI_MODEL`**). Deploy.
5. Open the service → **Settings** → **Networking** → **Generate domain** to get a URL like **`https://mutualfundrag-backend-production.up.railway.app`** (yours may differ).
6. Copy that URL into **`vercel.json`** (`rewrites` → `destination`) so `/api/*` proxies to Railway, and/or set Vercel **`API_BASE_URL`** to the same origin (see below).
7. **RAM:** The default **Hobby** tier may be tight for PyTorch + sentence-transformers + Chroma. If the service **OOMs**, increase memory in Railway **Settings** → **Resources** (or upgrade plan). This stack usually needs **about 1–2 GB** for a stable runtime.

**Pre-built image (optional, avoids long Docker builds on Railway’s free tier):**  
The workflow `.github/workflows/build-backend-image.yml` pushes **`ghcr.io/<your-github-username>/mutualfundrag-backend:latest`**. In Railway, create a service → **Deploy from Docker image** → image URL as above (make the GHCR package public or add a registry token). Add **`GEMINI_API_KEY`** in Variables.

**Auto-redeploy after GHCR push:** Add GitHub repository secrets **`RAILWAY_API_TOKEN`**, **`RAILWAY_SERVICE_ID`**, **`RAILWAY_ENVIRONMENT_ID`** (see [Railway API](https://docs.railway.app/guides/public-api) / dashboard). The workflow triggers a redeploy after each image push.

### Frontend on Vercel

1. In [Vercel](https://vercel.com), import the same GitHub repository.
2. Set **`API_BASE_URL`** in the Vercel project **Environment Variables** (Production):
   - **Recommended:** `https://YOUR-SERVICE.up.railway.app` (your Railway **public URL**, **no** trailing slash). The browser calls the API **directly**. CORS on the FastAPI app allows this and avoids **Vercel’s ~60s proxy timeout**, which can surface as **502** when the backend is cold and the first chat is slow.
   - **Alternative:** `/api` (default if unset) so requests go through **`vercel.json` rewrites** to Railway (same-origin). Simpler DNS-wise, but long cold starts + LLM time can hit the proxy limit and return **502**.
3. Deploy. The build runs `scripts/build-vercel.sh`, which injects `API_BASE_URL` and copies `phase5_frontend/` to `public/`. Set **Output Directory** to `public` if required.
4. The deployed site serves the chat UI. With **`/api`**, routes are proxied to Railway via `vercel.json`. With a **full Railway URL**, the UI talks to Railway without that hop.

**502 on chat:** Usually proxy timeout (use direct **`API_BASE_URL`** as above) or the Railway service still starting—wait and retry; the UI also retries 5xx a few times automatically.

### Keep the backend warm (optional cron)

If the Railway service idles and cold starts are slow, schedule an HTTP **GET** to **`https://YOUR-RAILWAY-URL/health`** every **10–15 minutes** (e.g. [cron-job.org](https://console.cron-job.org/), [UptimeRobot](https://uptimerobot.com)). Use a **timeout** of **120–180 seconds** on the first ping after long idle.

