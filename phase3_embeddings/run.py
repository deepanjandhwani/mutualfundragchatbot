"""Entry point: read Phase 2 chunks → embed → store in ChromaDB.

Run from project root:
  python -m phase3_embeddings.run
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from phase3_embeddings.config import (
    CHUNKS_DIR,
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
)
from phase3_embeddings.embedder import content_to_text, encode
from phase3_embeddings.chroma_client import (
    get_client,
    get_or_create_collection,
    upsert_chunks,
    clear_collection,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_chunks_from_disk(chunks_dir: Path) -> list[dict]:
    """Load all chunk JSON files from Phase 2 output."""
    chunks = []
    for path in sorted(chunks_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                chunks.append(json.load(f))
        except Exception as e:
            logger.warning("Skip %s: %s", path.name, e)
    return chunks


def main() -> None:
    logger.info("Phase 3: Embeddings & ChromaDB — loading chunks and embedding...")
    chunks_dir = CHUNKS_DIR
    if not chunks_dir.exists():
        logger.error("Chunks dir not found: %s. Run Phase 2 first.", chunks_dir)
        sys.exit(1)

    chunks = load_chunks_from_disk(chunks_dir)
    logger.info("Loaded %s chunks from %s", len(chunks), chunks_dir)
    if not chunks:
        logger.warning("No chunks to embed. Exiting.")
        sys.exit(0)

    # Prepare ids, documents, metadatas (content → text for embedding)
    ids = []
    documents = []
    metadatas = []
    for c in chunks:
        chunk_id = c.get("chunk_id")
        fund_id = c.get("fund_id", "")
        if not chunk_id:
            continue
        # Use composite id for idempotency: fund_id + chunk_id
        ids.append(f"{c.get('fund_id', '')}_{chunk_id}")
        documents.append(content_to_text(c.get("content", "")))
        metadatas.append({
            "fund_id": fund_id,
            "fund_name": str(c.get("fund_name", ""))[:500],
            "section": str(c.get("section", "")),
            "source_url": str(c.get("source_url", "")),
            "last_updated": str(c.get("last_updated", "")),
        })

    logger.info("Generating embeddings with model=%s ...", EMBEDDING_MODEL_NAME)
    embeddings = encode(documents, EMBEDDING_MODEL_NAME)
    logger.info("Generated %s embeddings", len(embeddings))

    client = get_client(CHROMA_PERSIST_DIR)
    collection = get_or_create_collection(client, COLLECTION_NAME)
    clear_collection(collection)
    upsert_chunks(collection, ids, embeddings, documents, metadatas)
    logger.info("Phase 3 done. ChromaDB at %s", CHROMA_PERSIST_DIR)


if __name__ == "__main__":
    main()
