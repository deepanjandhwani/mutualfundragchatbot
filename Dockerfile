# Backend-only image for Railway. Uses requirements-railway.txt (no Playwright).
# Ensures deps layer is cached when only code changes.
FROM python:3.11-slim

WORKDIR /app

# Install deps first (better layer cache)
COPY requirements-railway.txt .
RUN pip install --no-cache-dir -r requirements-railway.txt

# App code needed for RAG (shared config, phase3 chroma/embedder, phase4 API)
COPY shared ./shared
COPY phase3_embeddings ./phase3_embeddings
COPY phase4_backend ./phase4_backend

ENV PYTHONPATH=/app
EXPOSE 8000

# Railway sets PORT at runtime
CMD ["sh", "-c", "uvicorn phase4_backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
