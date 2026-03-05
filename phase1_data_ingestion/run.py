"""Entry point to run Phase 1 data ingestion.

Run from project root:
  python -m phase1_data_ingestion.run
Or (with project root on PYTHONPATH):
  python phase1_data_ingestion/run.py
"""

import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from phase1_data_ingestion.scraper import run_scraper
from phase1_data_ingestion.config import OUTPUT_DIR


def _ensure_playwright_browsers() -> bool:
    """Run 'playwright install chromium' so the browser exists. Returns True if OK to proceed."""
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            cwd=str(_PROJECT_ROOT),
            check=True,
            capture_output=True,
            timeout=120,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"Warning: could not install Playwright Chromium: {e}")
        print("If scraping fails, run manually: python -m playwright install chromium")
        return False


def main() -> None:
    print("Phase 1: Data ingestion — scraping IndMoney fund pages...")
    _ensure_playwright_browsers()
    results = run_scraper(output_dir=OUTPUT_DIR)
    print(
        f"Done. Success: {results['success']}, Failed: {results['failed']}. "
        f"Output dir: {OUTPUT_DIR}"
    )
    if results["failed_urls"]:
        print("Failed URLs:", results["failed_urls"])
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
