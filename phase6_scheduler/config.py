"""Phase 6: Scheduler configuration.

Cron schedule and paths for pipeline orchestration (Phase 1 → 2 → 3).
"""

from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Schedule: daily at 6 AM (cron: 0 6 * * *)
CRON_HOUR = 6
CRON_MINUTE = 0

# Pipeline runs from project root so all phase modules resolve
WORKING_DIR = _PROJECT_ROOT
