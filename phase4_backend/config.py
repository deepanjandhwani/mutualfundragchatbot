"""Phase 4: Backend RAG API configuration."""

import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.config import (
    PHASE3_CHROMA_PATH,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
)

# ChromaDB (same as Phase 3)
CHROMA_PERSIST_DIR = PHASE3_CHROMA_PATH
COLLECTION_NAME = CHROMA_COLLECTION_NAME
EMBEDDING_MODEL_NAME = EMBEDDING_MODEL

# GROQ
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# RAG (higher top_k so broad queries like "What is the NAV?" can cover all 8 funds)
RETRIEVAL_TOP_K = 16
MAX_ANSWER_SENTENCES = 3
# Cap sources shown in response (retrieved list is relevance-ordered; we show first N unique URLs)
MAX_SOURCES_DISPLAY = 5
