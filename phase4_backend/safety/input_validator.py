"""Block PII in user message. Used at query time only."""

from __future__ import annotations

from shared.constants import PII_PATTERNS, REFUSAL_PII


def contains_pii(text: str) -> bool:
    """Return True if text matches any PII pattern."""
    if not text or not text.strip():
        return False
    for pattern in PII_PATTERNS:
        if pattern.search(text):
            return True
    return False


def validate_user_message(message: str) -> tuple[bool, str | None]:
    """
    Validate user message for PII.
    Returns (is_valid, refusal_reason). If is_valid is False, refusal_reason is the message to return.
    """
    if not message or not message.strip():
        return False, "Please enter a question."
    if contains_pii(message):
        return False, REFUSAL_PII
    return True, None
