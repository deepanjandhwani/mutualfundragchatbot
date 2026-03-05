"""
Vercel entrypoint: expose the Phase 4 FastAPI app.
Static frontend is served from public/ (phase5_frontend copied at build).
"""
from phase4_backend.app import app

__all__ = ["app"]
