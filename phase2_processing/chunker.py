"""Phase 2: Turn parsed sections into Chunk objects."""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from shared.schemas import Chunk

from .config import CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS
from .parsers.overview_parser import parse_overview
from .parsers.performance_parser import parse_performance
from .parsers.allocation_parser import parse_asset_allocation, parse_sector_allocation
from .parsers.holdings_parser import parse_holdings
from .parsers.faq_parser import parse_faq
from .parsers.about_parser import parse_about

logger = logging.getLogger(__name__)


def _split_long_text(text: str) -> List[str]:
    """Split long text into overlapping chunks."""
    if not text:
        return []
    if len(text) <= CHUNK_MAX_CHARS:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_MAX_CHARS
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start = end - CHUNK_OVERLAP_CHARS
    return chunks


def build_chunks_for_fund(fund_doc: Dict) -> List[Chunk]:
    """Create Chunk objects for all sections of a single fund."""
    fund_id = str(fund_doc.get("fund_id", "")).strip()
    fund_name = str(fund_doc.get("fund_name", "")).strip()
    url = str(fund_doc.get("url", "")).strip()
    scraped_at = str(fund_doc.get("scraped_at", ""))  # ISO string

    try:
        last_updated_date = scraped_at.split("T", 1)[0] if "T" in scraped_at else scraped_at
    except Exception:
        last_updated_date = scraped_at

    chunks: List[Chunk] = []

    def add_text_chunks(section: str, texts: Iterable[str]) -> None:
        nonlocal chunks
        for text in texts:
            for split_idx, piece in enumerate(_split_long_text(text), start=1):
                chunk_id = f"{fund_id}_{section}_{len(chunks) + 1}"
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        fund_id=fund_id,
                        fund_name=fund_name,
                        section=section,
                        content=piece,
                        source_url=url,
                        last_updated=last_updated_date,
                    )
                )

    # Overview
    add_text_chunks("overview", parse_overview(fund_doc))

    # Performance
    add_text_chunks("performance", parse_performance(fund_doc))

    # Asset allocation & changes
    add_text_chunks("asset_allocation", parse_asset_allocation(fund_doc))

    # Sector allocation
    add_text_chunks("sector_allocation", parse_sector_allocation(fund_doc))

    # Holdings & portfolio changes
    add_text_chunks("holdings", parse_holdings(fund_doc))

    # FAQ
    add_text_chunks("faq", parse_faq(fund_doc))

    # About (JSON content)
    about_objs = parse_about(fund_doc)
    for about_idx, about_obj in enumerate(about_objs, start=1):
        chunk_id = f"{fund_id}_about_{about_idx}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                fund_id=fund_id,
                fund_name=fund_name,
                section="about",
                content=about_obj,  # dict → will be JSON in output files
                source_url=url,
                last_updated=last_updated_date,
            )
        )

    logger.info("Built %s chunks for fund_id=%s", len(chunks), fund_id)
    return chunks


def save_chunks_to_disk(chunks: Iterable[Chunk], output_dir: Path) -> None:
    """Persist chunks as JSON files under output_dir."""
    import json

    output_dir.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        file_name = f"{chunk.fund_id}_{chunk.chunk_id}.json"
        path = output_dir / file_name
        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(chunk), f, ensure_ascii=False, indent=2)

