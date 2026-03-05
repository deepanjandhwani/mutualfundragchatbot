"""PII validation helpers.

Used at query time (Phase 4) to reject user messages that contain PII (PAN, Aadhaar,
account numbers, OTPs, email, phone). Not used when loading or storing scraped fund data
(Phase 2); scraped content is trusted as factual fund information.
"""

from __future__ import annotations

import logging
from typing import Iterable

from shared.constants import PII_PATTERNS
from shared.schemas import Chunk

logger = logging.getLogger(__name__)


def contains_pii(text: str) -> bool:
    """Return True if text matches any PII pattern."""
    if not text:
        return False
    for pattern in PII_PATTERNS:
        if pattern.search(text):
            return True
    return False


def validate_chunks(chunks: Iterable[Chunk]) -> list[Chunk]:
    """Filter out chunks that contain PII."""
    safe_chunks: list[Chunk] = []
    for chunk in chunks:
        content_repr = chunk.content
        if isinstance(content_repr, dict):
            # Join values for PII scanning
            joined = " ".join(str(v) for v in content_repr.values())
        else:
            joined = str(content_repr)

        if contains_pii(joined):
            logger.warning("Dropping chunk %s due to suspected PII.", chunk.chunk_id)
            continue
        safe_chunks.append(chunk)
    return safe_chunks

