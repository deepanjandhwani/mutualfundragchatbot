"""Extract high-level overview text for a fund."""

from __future__ import annotations

from typing import Dict, List

from .utils import extract_between, normalise_whitespace


def parse_overview(fund_doc: Dict) -> List[str]:
    """Return one or more overview snippets for the fund.

    Strategy:
    - Use `extracted_sections["overview"]` from Phase 1.
    - Try to extract the dedicated "Overview" section if present.
    - Fallback to a trimmed prefix of the full text.
    """
    sections = fund_doc.get("extracted_sections") or {}
    full_text: str = sections.get("overview") or ""

    fund_name = fund_doc.get("fund_name", "").strip()
    overview_snippets: List[str] = []

    # Try markers like "<Fund Name> Overview" or generic "Fund Overview"
    markers = []
    if fund_name:
        markers.append(f"{fund_name} Overview")
    markers.append("Fund Overview")

    overview_text = ""
    for marker in markers:
        overview_text = extract_between(full_text, f"{marker}\n", "About ")
        if overview_text:
            break

    if not overview_text:
        # Fallback: first ~1200 characters of the page text
        overview_text = full_text[:1200]

    overview_text = normalise_whitespace(overview_text)
    if overview_text:
        overview_snippets.append(overview_text)

    return overview_snippets

