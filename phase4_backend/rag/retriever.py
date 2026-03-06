"""ChromaDB retrieval for RAG."""

from __future__ import annotations

import re
from pathlib import Path
import sys

# Ensure project root on path for phase3 imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from phase3_embeddings.chroma_client import get_client, get_or_create_collection, query_collection
from phase3_embeddings.embedder import encode

# Short/partial name → full canonical name used in ChromaDB chunks.
# Keys must be lowercase. Checked in order; first match wins.
_FUND_ALIASES: list[tuple[str, str]] = [
    ("large and mid cap", "HDFC Large and Mid Cap Fund"),
    ("large & mid cap", "HDFC Large and Mid Cap Fund"),
    ("largemidcap 250", "HDFC Nifty LargeMidcap 250 Index Fund"),
    ("large midcap 250", "HDFC Nifty LargeMidcap 250 Index Fund"),
    ("largemidcap", "HDFC Nifty LargeMidcap 250 Index Fund"),
    ("nifty next 50", "HDFC Nifty Next 50 Index Fund"),
    ("next 50", "HDFC Nifty Next 50 Index Fund"),
    ("large cap", "HDFC Large Cap Fund"),
    ("largecap", "HDFC Large Cap Fund"),
    ("flexi cap", "HDFC Flexi Cap Fund"),
    ("flexicap", "HDFC Flexi Cap Fund"),
    ("elss tax saver", "HDFC ELSS TaxSaver Fund"),
    ("elss taxsaver", "HDFC ELSS TaxSaver Fund"),
    ("elss", "HDFC ELSS TaxSaver Fund"),
    ("tax saver", "HDFC ELSS TaxSaver Fund"),
    ("taxsaver", "HDFC ELSS TaxSaver Fund"),
    ("mid cap", "HDFC Mid Cap Fund"),
    ("midcap", "HDFC Mid Cap Fund"),
    ("housing", "HDFC Housing Opportunities Fund"),
]


def _expand_fund_aliases(query: str) -> str:
    """Replace short fund name references with canonical full names for better retrieval."""
    q_lower = query.lower()
    for alias, full_name in _FUND_ALIASES:
        if alias in q_lower:
            pattern = re.compile(re.escape(alias), re.IGNORECASE)
            return pattern.sub(full_name, query, count=1)
    return query


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
    query = _expand_fund_aliases(query)
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
