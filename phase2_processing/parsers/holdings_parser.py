"""Extract holdings and portfolio changes text for a fund."""

from __future__ import annotations

from typing import Dict, List

from .utils import extract_between, normalise_whitespace


def parse_holdings(fund_doc: Dict) -> List[str]:
    """Return snippets for holdings table and portfolio changes."""
    sections = fund_doc.get("extracted_sections") or {}
    full_text: str = sections.get("overview") or ""

    text = extract_between(
        full_text,
        "Holdings Details",
        "HDFC ELSS TaxSaver Fund Overview",
    )
    if not text:
        text = extract_between(full_text, "Holdings", "Overview")

    text = normalise_whitespace(text)
    return [text] if text else []

