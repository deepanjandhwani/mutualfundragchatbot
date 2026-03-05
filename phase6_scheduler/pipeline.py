"""Phase 6: Run full pipeline (Phase 1 → Phase 2 → Phase 3) and write last_updated for frontend."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from shared.config import LAST_REFRESH_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _run_phase(module_name: str, working_dir: Path) -> bool:
    """Run a phase as a subprocess. Returns True on success. Streams output in CI for visibility."""
    cmd = [sys.executable, "-m", module_name]
    # In CI (e.g. GitHub Actions) stream stdout/stderr so logs are visible
    in_ci = os.environ.get("CI", "").lower() in ("1", "true", "yes")
    capture = not in_ci
    try:
        result = subprocess.run(
            cmd,
            cwd=str(working_dir),
            capture_output=capture,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            if capture and (result.stderr or result.stdout):
                logger.error("%s failed (exit %s): %s", module_name, result.returncode, (result.stderr or result.stdout)[:2000])
            else:
                logger.error("%s failed with exit code %s.", module_name, result.returncode)
            return False
        logger.info("%s completed successfully.", module_name)
        return True
    except subprocess.TimeoutExpired:
        logger.error("%s timed out.", module_name)
        return False
    except Exception as e:
        logger.exception("Error running %s: %s", module_name, e)
        return False


def write_last_refresh(refresh_file: Path) -> None:
    """Write last_updated timestamp so backend/frontend can show when data was last fetched."""
    now = datetime.now(timezone.utc)
    data = {
        "last_updated": now.strftime("%Y-%m-%d"),
        "updated_at_iso": now.isoformat(),
    }
    refresh_file.parent.mkdir(parents=True, exist_ok=True)
    with refresh_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Wrote last refresh: %s -> %s", data["last_updated"], refresh_file)


def run_pipeline(working_dir: Path | None = None) -> bool:
    """Run Phase 1 → Phase 2 → Phase 3. On success, write last_refresh.json. Returns True if all succeeded."""
    wd = working_dir or _PROJECT_ROOT
    refresh_file = LAST_REFRESH_FILE

    logger.info("Phase 6: Starting pipeline (1 → 2 → 3)...")

    if not _run_phase("phase1_data_ingestion.run", wd):
        return False
    if not _run_phase("phase2_processing.run", wd):
        return False
    if not _run_phase("phase3_embeddings.run", wd):
        return False

    write_last_refresh(refresh_file)
    logger.info("Phase 6: Pipeline completed. Last refresh written to %s", refresh_file)
    return True


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
