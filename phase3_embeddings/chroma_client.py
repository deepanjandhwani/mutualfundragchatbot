"""ChromaDB collection setup, upsert, and query."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


def get_client(persist_directory: Path):
    """Return a ChromaDB PersistentClient."""
    persist_directory = Path(persist_directory)
    persist_directory.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(persist_directory),
        settings=Settings(anonymized_telemetry=False),
    )


def get_or_create_collection(client, collection_name: str):
    """Get or create the named collection."""
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "IndMoney fund chunks for RAG"},
    )


def upsert_chunks(
    collection,
    ids: List[str],
    embeddings: List[List[float]],
    documents: List[str],
    metadatas: List[dict],
) -> None:
    """Upsert chunk documents with embeddings and metadata."""
    # ChromaDB metadata values must be str, int, float or bool
    clean_metadatas = []
    for m in metadatas:
        clean = {k: (v if isinstance(v, (str, int, float, bool)) else str(v)) for k, v in m.items()}
        clean_metadatas.append(clean)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=clean_metadatas,
    )
    logger.info("Upserted %s chunks", len(ids))


def query_collection(
    collection,
    query_embeddings: List[List[float]],
    n_results: int = 5,
    where: Optional[dict] = None,
) -> dict:
    """Query by embedding; optional metadata filter (e.g. where={"fund_id": "2989"})."""
    kwargs = {
        "query_embeddings": query_embeddings,
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where is not None:
        kwargs["where"] = where
    return collection.query(**kwargs)


def clear_collection(collection) -> None:
    """Remove all documents in the collection (for full refresh)."""
    # Chroma doesn't have clear(); we get all ids and delete
    try:
        result = collection.get(include=[])
        ids = result["ids"]
        if ids:
            collection.delete(ids=ids)
            logger.info("Cleared %s documents from collection", len(ids))
    except Exception as e:
        logger.warning("Clear collection: %s", e)
