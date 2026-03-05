"""FastAPI app for Phase 4 RAG API."""

import os
from pathlib import Path

# Load .env from project root (parent of phase4_backend); then cwd so env is set before config imports
try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parents[1]
    load_dotenv(_root / ".env")
    load_dotenv()  # cwd as fallback (e.g. Vercel)
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from phase4_backend.routes.chat import router as chat_router
from phase4_backend.routes.meta import router as meta_router

app = FastAPI(
    title="IndMoney Fund Facts API",
    description="Facts-only RAG API for HDFC mutual fund information. No investment advice.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router, prefix="", tags=["chat"])
app.include_router(meta_router, prefix="", tags=["meta"])


@app.get("/")
def root():
    """Redirect to API docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "groq_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
    }
