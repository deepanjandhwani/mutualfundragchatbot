"""Detect opinionated and comparison queries to refuse."""

from __future__ import annotations

import re

from shared.constants import (
    REFUSAL_OPINION,
    REFUSAL_COMPARE,
    EDUCATIONAL_LINK,
)


def _matches_any(text: str, patterns: list[str]) -> bool:
    if not text:
        return False
    lower = text.lower().strip()
    for pat in patterns:
        if re.search(pat, lower, re.IGNORECASE):
            return True
    return False


OPINION_PATTERNS = [
    r"should\s+i\s+(buy|sell|invest)",
    r"(buy|sell|invest)\s+(in|into)\s+",
    r"is\s+it\s+(good|bad)\s+to",
    r"\brecommend\b",
    r"\badvice\b",
    r"opinion\s+on",
    r"what\s+do\s+you\s+think",
]

COMPARE_PATTERNS = [
    r"compare\s+(returns?|performance)",
    r"which\s+(fund|one)\s+(is\s+)?better",
    r"calculate\s+(returns?|performance)",
    r"compute\s+(returns?|performance)",
]


def is_opinionated_query(message: str) -> bool:
    """True if the user is asking for advice or opinion."""
    return _matches_any(message, OPINION_PATTERNS)


def is_compare_query(message: str) -> bool:
    """True if the user wants to compare or compute returns."""
    return _matches_any(message, COMPARE_PATTERNS)


def classify_query(message: str) -> tuple[str, str | None]:
    """
    Classify user query. Returns (action, refusal_message).
    action: "refuse_opinion" | "refuse_compare" | "answer"
    refusal_message: message to return if refusing, else None.
    """
    if is_opinionated_query(message):
        return "refuse_opinion", f"{REFUSAL_OPINION}"
    if is_compare_query(message):
        return "refuse_compare", REFUSAL_COMPARE
    return "answer", None
