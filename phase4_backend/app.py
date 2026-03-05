"""FastAPI app for Phase 4 RAG API."""

from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
def health():
    return {"status": "ok"}
