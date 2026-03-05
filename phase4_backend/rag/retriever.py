"""ChromaDB retrieval for RAG."""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure project root on path for phase3 imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from phase3_embeddings.chroma_client import get_client, get_or_create_collection, query_collection
from phase3_embeddings.embedder import encode


def retrieve(
    query: str,
    chroma_persist_dir: Path,
    collection_name: str,
    embedding_model_name: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Embed the query, search ChromaDB, return list of dicts with document, metadata (source_url, fund_name, etc.).
    """
    client = get_client(chroma_persist_dir)
    collection = get_or_create_collection(client, collection_name)
    query_embeddings = encode([query], embedding_model_name)
    if not query_embeddings:
        return []
    result = query_collection(collection, query_embeddings, n_results=top_k)
    # result: ids, documents, metadatas, distances (each list of lists for single query)
    docs = result.get("documents", [[]])[0] or []
    metadatas = result.get("metadatas", [[]])[0] or []
    out = []
    for i, doc in enumerate(docs):
        meta = metadatas[i] if i < len(metadatas) else {}
        out.append({
            "document": doc,
            "source_url": meta.get("source_url", ""),
            "fund_name": meta.get("fund_name", ""),
            "fund_id": meta.get("fund_id", ""),
            "section": meta.get("section", ""),
            "last_updated": meta.get("last_updated", ""),
        })
    return out
