"""Phase 3: Embeddings & ChromaDB configuration."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.config import (
    PHASE2_OUTPUT,
    PHASE3_CHROMA_PATH,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
)

# Phase 2 chunks (input)
CHUNKS_DIR = PHASE2_OUTPUT

# ChromaDB persistent storage
CHROMA_PERSIST_DIR = PHASE3_CHROMA_PATH

# Collection and model
COLLECTION_NAME = CHROMA_COLLECTION_NAME
EMBEDDING_MODEL_NAME = EMBEDDING_MODEL
