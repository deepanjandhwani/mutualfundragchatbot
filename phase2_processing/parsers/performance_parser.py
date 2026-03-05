"""Extract performance-related text for a fund."""

from __future__ import annotations

from typing import Dict, List

from .utils import extract_between, normalise_whitespace


def parse_performance(fund_doc: Dict) -> List[str]:
    """Return performance snippets (1Y, 3Y, etc.) from the overview text."""
    sections = fund_doc.get("extracted_sections") or {}
    full_text: str = sections.get("overview") or ""

    snippets: List[str] = []

    perf_text = extract_between(
        full_text,
        "HDFC",
        "HDFC ELSS TaxSaver Fund Asset Allocation",
    )
    # The above is tailored to the sample page; fall back to generic markers
    if not perf_text:
        perf_text = extract_between(full_text, "Performance", "Asset Allocation")

    perf_text = normalise_whitespace(perf_text)
    if perf_text:
        snippets.append(perf_text[:1600])

    return snippets

