"""Utility functions for section parsing."""

from __future__ import annotations

from typing import Optional


def extract_between(text: str, start_marker: str, end_marker: Optional[str] = None) -> str:
    """Extract substring between start_marker and end_marker (if present).

    If start_marker is not found, returns an empty string.
    If end_marker is not found, returns text from start_marker to end.
    """
    if not text:
        return ""
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return ""
    start_idx += len(start_marker)
    if end_marker:
        end_idx = text.find(end_marker, start_idx)
        if end_idx == -1:
            end_idx = len(text)
    else:
        end_idx = len(text)
    return text[start_idx:end_idx].strip()


def normalise_whitespace(text: str) -> str:
    """Collapse excessive whitespace while preserving line breaks where useful."""
    if not text:
        return ""
    # Replace tabs with spaces and strip trailing spaces per line
    lines = [line.rstrip() for line in text.replace("\t", " ").splitlines()]
    # Collapse consecutive empty lines
    cleaned_lines = []
    empty_streak = 0
    for line in lines:
        if line.strip():
            empty_streak = 0
            cleaned_lines.append(line)
        else:
            if empty_streak == 0:
                cleaned_lines.append("")
            empty_streak += 1
    return "\n".join(cleaned_lines).strip()

