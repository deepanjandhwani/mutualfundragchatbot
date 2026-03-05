"""
Vercel serverless function: expose the Phase 4 FastAPI app.
Must live in api/ so Vercel matches it as a Serverless Function.
Mounted at /api/app so /api/app/chat, /api/app/meta, etc. work.
"""
from fastapi import FastAPI
from phase4_backend.app import app as backend_app

app = FastAPI()
app.mount("/api/app", backend_app)

__all__ = ["app"]
