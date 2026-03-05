"""Extract FAQ text for a fund."""

from __future__ import annotations

from typing import Dict, List

from .utils import extract_between, normalise_whitespace


def parse_faq(fund_doc: Dict) -> List[str]:
    """Return snippets for the FAQ section."""
    sections = fund_doc.get("extracted_sections") or {}
    full_text: str = sections.get("overview") or ""

    text = extract_between(
        full_text,
        "Frequently Asked Questions",
        "Mutual Fund execution provided by",
    )
    if not text:
        text = extract_between(full_text, "FAQs", "Mutual Fund execution provided by")

    text = normalise_whitespace(text)
    return [text] if text else []

