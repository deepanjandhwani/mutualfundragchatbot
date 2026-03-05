"""Phase 6: Single pipeline run or scheduled job entry point.

Run from project root:
  python -m phase6_scheduler.run

Optional: use APScheduler for periodic runs (e.g. daily 6 AM).
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from phase6_scheduler.config import WORKING_DIR
from phase6_scheduler.pipeline import run_pipeline


def main() -> None:
    print("Phase 6: Running data refresh pipeline (Phase 1 → 2 → 3)...")
    success = run_pipeline(working_dir=WORKING_DIR)
    if success:
        print("Pipeline completed. Data last_updated has been written for the frontend.")
    else:
        print("Pipeline failed. Check logs above.")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
