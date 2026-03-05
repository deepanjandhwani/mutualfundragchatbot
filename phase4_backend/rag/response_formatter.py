"""Format RAG response: answer ≤3 sentences, sources array."""

from __future__ import annotations


# Suffixes to strip from fund names when matching against answer text
_FUND_NAME_SUFFIXES = (
    " Direct Plan Growth",
    " Direct Growth",
    " Growth Option",
    " - IndMoney",
)


def _normalize_for_match(text: str) -> str:
    """Normalize so 'TaxSaver' and 'Tax Saver' etc. match."""
    if not text:
        return ""
    t = text.lower().strip()
    t = t.replace("taxsaver", "tax saver").replace("tax-saver", "tax saver")
    return " ".join(t.split())


def _fund_mentioned_in_answer(fund_name: str, answer: str) -> bool:
    """Return True if the fund is mentioned in the answer (normalized name or first 4 words)."""
    if not answer or not fund_name:
        return False
    answer_norm = _normalize_for_match(answer)
    name = (fund_name or "").strip()
    for suffix in _FUND_NAME_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
        name = name.replace(suffix, "").strip()
    name_norm = _normalize_for_match(name)
    if name_norm in answer_norm:
        return True
    words = name.split()[:4]
    if words:
        key = _normalize_for_match(" ".join(words))
        if key in answer_norm:
            return True
    return False


def _query_matches_fund(query: str, fund_name: str, fund_id: str) -> bool:
    """True if the user query clearly refers to this fund (for fallback when answer match fails)."""
    if not query or not fund_name:
        return False
    q = _normalize_for_match(query)
    name = (fund_name or "").lower()
    # Direct substring: e.g. "elss" in query and "elss" in fund name
    if name in q or q in name:
        return True
    # Token overlap: "expense ratio hdfc elss" -> "elss" matches "HDFC ELSS Tax Saver..."
    for word in q.split():
        if len(word) >= 3 and word in name:
            return True
    if fund_id and fund_id in query:
        return True
    return False


def format_sources(
    retrieved: list[dict],
    answer: str | None = None,
    query: str | None = None,
    max_sources: int | None = None,
) -> list[dict]:
    """
    Build unique sources list from retrieved chunks (relevance-ordered).
    If answer is provided, include sources for funds mentioned in the answer.
    If that yields no sources and query is provided, fall back to query-based match.
    Optionally cap at max_sources.
    """
    seen = set()
    sources = []
    for r in retrieved:
        url = (r.get("source_url") or "").strip()
        fund_name = (r.get("fund_name") or "Fund").strip()
        fund_id = (r.get("fund_id") or "").strip()
        if not url or url in seen:
            continue
        if answer is not None and not _fund_mentioned_in_answer(fund_name, answer):
            continue
        if max_sources is not None and len(sources) >= max_sources:
            break
        seen.add(url)
        sources.append({"url": url, "label": f"{fund_name} - IndMoney"})
    # Fallback: if no sources from answer match, use query to include relevant fund sources
    if not sources and query and retrieved:
        for r in retrieved:
            url = (r.get("source_url") or "").strip()
            fund_name = (r.get("fund_name") or "Fund").strip()
            fund_id = (r.get("fund_id") or "").strip()
            if not url or url in seen:
                continue
            if not _query_matches_fund(query, fund_name, fund_id):
                continue
            if max_sources is not None and len(sources) >= max_sources:
                break
            seen.add(url)
            sources.append({"url": url, "label": f"{fund_name} - IndMoney"})
    return sources


def ensure_last_updated_suffix(answer: str) -> str:
    """Append 'Last updated from sources.' if not already present."""
    if not answer or not answer.strip():
        return "Last updated from sources."
    text = answer.strip()
    suffix = "Last updated from sources."
    if not text.endswith(suffix):
        text = f"{text} {suffix}"
    return text
