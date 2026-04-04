"""Background warmup so Uvicorn can accept connections before the embedding model is loaded."""

from __future__ import annotations

import logging
import threading

log = logging.getLogger(__name__)

_ready = threading.Event()


def _run_warmup() -> None:
    try:
        from phase4_backend import config
        from phase3_embeddings.embedder import get_embedding_model
        from phase3_embeddings.chroma_client import get_client, get_or_create_collection

        log.info("Warming up embedding model...")
        get_embedding_model(config.EMBEDDING_MODEL_NAME)
        log.info("Warming up ChromaDB connection...")
        client = get_client(config.CHROMA_PERSIST_DIR)
        get_or_create_collection(client, config.COLLECTION_NAME)
        log.info("Warmup complete.")
    except Exception:
        log.exception("Warmup failed")
    finally:
        _ready.set()


def start_background_warmup() -> None:
    """Start embedding + Chroma load in a daemon thread; return immediately."""
    t = threading.Thread(target=_run_warmup, daemon=True)
    t.start()


def is_ready() -> bool:
    return _ready.is_set()


def wait_until_ready(timeout: float | None = None) -> bool:
    """Block until warmup finished or timeout (seconds). Returns True if ready."""
    return _ready.wait(timeout=timeout)
