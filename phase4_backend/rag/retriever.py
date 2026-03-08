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


_ALIAS_TO_FUND_ID: list[tuple[str, str, str]] = [
    ("large and mid cap", "HDFC Large and Mid Cap Fund", "2874"),
    ("large & mid cap", "HDFC Large and Mid Cap Fund", "2874"),
    ("largemidcap 250", "HDFC Nifty LargeMidcap 250 Index Fund", "1047724"),
    ("large midcap 250", "HDFC Nifty LargeMidcap 250 Index Fund", "1047724"),
    ("largemidcap", "HDFC Nifty LargeMidcap 250 Index Fund", "1047724"),
    ("nifty largemidcap", "HDFC Nifty LargeMidcap 250 Index Fund", "1047724"),
    ("nifty next 50", "HDFC Nifty Next 50 Index Fund", "1040010"),
    ("next 50", "HDFC Nifty Next 50 Index Fund", "1040010"),
    ("large cap", "HDFC Large Cap Fund", "2989"),
    ("largecap", "HDFC Large Cap Fund", "2989"),
    ("flexi cap", "HDFC Flexi Cap Fund", "3184"),
    ("flexicap", "HDFC Flexi Cap Fund", "3184"),
    ("elss tax saver", "HDFC ELSS TaxSaver Fund", "2685"),
    ("elss taxsaver", "HDFC ELSS TaxSaver Fund", "2685"),
    ("elss", "HDFC ELSS TaxSaver Fund", "2685"),
    ("tax saver", "HDFC ELSS TaxSaver Fund", "2685"),
    ("taxsaver", "HDFC ELSS TaxSaver Fund", "2685"),
    ("mid cap", "HDFC Mid Cap Fund", "3097"),
    ("midcap", "HDFC Mid Cap Fund", "3097"),
    ("housing", "HDFC Housing Opportunities Fund", "9006"),
]


def detect_mentioned_funds(query: str) -> list[tuple[str, str]]:
    """Return list of (fund_id, fund_name) for funds mentioned in the query."""
    q_lower = query.lower()
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for alias, name, fid in _ALIAS_TO_FUND_ID:
        if alias in q_lower and fid not in seen:
            seen.add(fid)
            result.append((fid, name))
    return result


def _expand_fund_aliases(query: str) -> str:
    """Replace short fund name references with canonical full names for better retrieval."""
    q_lower = query.lower()
    for alias, full_name in _FUND_ALIASES:
        if alias in q_lower:
            pattern = re.compile(re.escape(alias), re.IGNORECASE)
            return pattern.sub(full_name, query, count=1)
    return query


def _query_single(collection, query_embeddings, top_k: int, where=None) -> list[dict]:
    """Run a single ChromaDB query and return list of result dicts."""
    result = query_collection(collection, query_embeddings, n_results=top_k, where=where)
    docs = result.get("documents", [[]])[0] or []
    metadatas = result.get("metadatas", [[]])[0] or []
    distances = result.get("distances", [[]])[0] or []
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
            "_distance": distances[i] if i < len(distances) else 999,
        })
    return out


def retrieve(
    query: str,
    chroma_persist_dir: Path,
    collection_name: str,
    embedding_model_name: str,
    top_k: int = 5,
    fund_ids: list[str] | None = None,
) -> list[dict]:
    """
    Embed the query, search ChromaDB, return list of dicts with document, metadata.
    When multiple funds are involved, queries per-fund to guarantee representation.
    """
    from shared.config import FUND_URLS

    query = _expand_fund_aliases(query)
    client = get_client(chroma_persist_dir)
    collection = get_or_create_collection(client, collection_name)
    query_embeddings = encode([query], embedding_model_name)
    if not query_embeddings:
        return []

    if fund_ids and len(fund_ids) == 1:
        return _query_single(collection, query_embeddings, top_k, where={"fund_id": fund_ids[0]})

    ids_to_query = fund_ids if fund_ids else [f["id"] for f in FUND_URLS]
    per_fund_k = max(3, top_k // len(ids_to_query))
    merged: list[dict] = []
    seen_docs: set[str] = set()
    for fid in ids_to_query:
        rows = _query_single(collection, query_embeddings, per_fund_k, where={"fund_id": fid})
        for row in rows:
            doc_key = row["document"][:120]
            if doc_key not in seen_docs:
                seen_docs.add(doc_key)
                merged.append(row)

    merged.sort(key=lambda r: r.get("_distance", 999))
    return merged
