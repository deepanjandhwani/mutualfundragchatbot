"""Entry point to run Phase 2 processing.

Reads Phase 1 JSON outputs and writes structured chunks for embeddings.

Run from project root:
  python -m phase2_processing.run
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from dataclasses import asdict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from phase2_processing.config import INPUT_DIR, OUTPUT_DIR, OUTPUT_DIR_FUND_WISE  # type: ignore  # noqa: E402
from phase2_processing.chunker import build_chunks_for_fund, save_chunks_to_disk  # type: ignore  # noqa: E402
from phase2_processing.fund_wise_export import run_fund_wise_export  # type: ignore  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _load_fund_docs(input_dir: Path) -> list[dict]:
    docs: list[dict] = []
    for path in sorted(input_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                docs.append(json.load(f))
        except Exception as exc:
            logger.warning("Failed to load %s: %s", path.name, exc)
    return docs


def main() -> None:
    logger.info("Phase 2: Processing — building structured chunks...")
    input_dir = INPUT_DIR
    output_dir = OUTPUT_DIR

    fund_docs = _load_fund_docs(input_dir)
    logger.info("Loaded %s fund documents from %s", len(fund_docs), input_dir)

    all_chunks = []
    for doc in fund_docs:
        fund_chunks = build_chunks_for_fund(doc)
        all_chunks.extend(fund_chunks)

    logger.info("Built %s chunks", len(all_chunks))
    # PII filtering is not applied when loading data; it is applied only to user input at query time (Phase 4).
    save_chunks_to_disk(all_chunks, output_dir)
    logger.info("Saved chunks to %s", output_dir)

    # One JSON per fund for viewing/verification
    n_funds = run_fund_wise_export(output_dir, OUTPUT_DIR_FUND_WISE)
    logger.info("Saved %s fund-wise JSONs to %s", n_funds, OUTPUT_DIR_FUND_WISE)


if __name__ == "__main__":
    main()

