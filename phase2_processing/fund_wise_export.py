"""Export one JSON per fund for viewing and verification."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def build_fund_wise_json(chunks_dir: Path) -> dict[str, dict[str, Any]]:
    """
    Read all chunk JSONs from chunks_dir, group by fund_id, and return
    a dict: fund_id -> { fund_id, fund_name, source_url, last_updated, sections }.
    """
    funds: dict[str, dict[str, Any]] = {}

    for path in sorted(chunks_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                chunk = json.load(f)
        except Exception as e:
            logger.warning("Skip %s: %s", path.name, e)
            continue

        fund_id = chunk.get("fund_id", "")
        if not fund_id:
            continue

        if fund_id not in funds:
            funds[fund_id] = {
                "fund_id": fund_id,
                "fund_name": chunk.get("fund_name", ""),
                "source_url": chunk.get("source_url", ""),
                "last_updated": chunk.get("last_updated", ""),
                "sections": {},
            }

        section = chunk.get("section", "other")
        content = chunk.get("content")

        if section not in funds[fund_id]["sections"]:
            funds[fund_id]["sections"][section] = []

        # Append content (string or dict for 'about')
        funds[fund_id]["sections"][section].append(content)

    return funds


def save_fund_wise(funds: dict[str, dict[str, Any]], output_dir: Path) -> None:
    """Write one JSON file per fund to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for fund_id, data in funds.items():
        out_path = output_dir / f"{fund_id}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Wrote %s", out_path.name)


def run_fund_wise_export(chunks_dir: Path, output_dir: Path) -> int:
    """Build fund-wise JSONs from chunks and save. Returns number of funds written."""
    funds = build_fund_wise_json(chunks_dir)
    save_fund_wise(funds, output_dir)
    return len(funds)
