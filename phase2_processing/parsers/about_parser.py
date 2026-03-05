"""Extract ABOUT section as readable JSON."""

from __future__ import annotations

import json
from typing import Dict, List, Any

from .utils import extract_between, normalise_whitespace


def parse_about(fund_doc: Dict) -> List[Any]:
    """Return a JSON-serialisable object for the About section.

    The returned list typically has a single dict like:

    {
        "summary": "...",
        "fund_objective": "...",
        "fund_managers": "...",
        "taxation": "...",
    }
    """
    sections = fund_doc.get("extracted_sections") or {}
    full_text: str = sections.get("overview") or ""
    fund_name: str = fund_doc.get("fund_name", "").strip()

    # Try to isolate the About block between 'About <Fund Name>' and 'Key Parameters'
    start_marker_candidates = []
    if fund_name:
        start_marker_candidates.append(f"About {fund_name}")
    start_marker_candidates.append("About ")

    about_raw = ""
    for marker in start_marker_candidates:
        about_raw = extract_between(full_text, marker, "Key Parameters")
        if about_raw:
            break

    if not about_raw:
        # Fallback: from "About" to "Frequently Asked Questions"
        about_raw = extract_between(full_text, "About", "Frequently Asked Questions")

    about_raw = normalise_whitespace(about_raw)
    if not about_raw:
        return []

    # Heuristic splitting inside about_raw
    summary = about_raw

    # Attempt to extract some sub-parts by simple markers
    objective = ""
    if "Investment objective" in about_raw:
        objective = extract_between(about_raw, "Investment objective", "Minimum Investment")

    taxation = ""
    if "Taxation" in about_raw:
        taxation = extract_between(about_raw, "Taxation", "Investment objective")

    fund_managers = ""
    if "Fund Manager" in about_raw:
        fund_managers = extract_between(about_raw, "Fund Manager", "Learn more")

    about_json = {
        "summary": summary,
        "fund_objective": objective or None,
        "fund_managers": fund_managers or None,
        "taxation": taxation or None,
    }

    # Ensure it is JSON-serialisable
    json.dumps(about_json, ensure_ascii=False)

    return [about_json]

