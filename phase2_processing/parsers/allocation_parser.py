"""Extract asset and sector allocation text for a fund."""

from __future__ import annotations

from typing import Dict, List

from .utils import extract_between, normalise_whitespace


def parse_asset_allocation(fund_doc: Dict) -> List[str]:
    """Return snippets describing asset allocation and allocation changes."""
    sections = fund_doc.get("extracted_sections") or {}
    full_text: str = sections.get("overview") or ""

    text = extract_between(
        full_text,
        "Asset Allocation",
        "HDFC ELSS TaxSaver Fund Sector Allocation",
    )
    if not text:
        text = extract_between(full_text, "Asset Allocation", "Sector Allocation")

    text = normalise_whitespace(text)
    return [text] if text else []


def parse_sector_allocation(fund_doc: Dict) -> List[str]:
    """Return snippets describing sector allocation and sector changes."""
    sections = fund_doc.get("extracted_sections") or {}
    full_text: str = sections.get("overview") or ""

    text = extract_between(
        full_text,
        "Sector Allocation",
        "Holdings Details",
    )
    if not text:
        text = extract_between(full_text, "Sector Allocation", "Holdings")

    text = normalise_whitespace(text)
    return [text] if text else []

