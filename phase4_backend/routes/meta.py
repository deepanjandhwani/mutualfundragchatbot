"""Meta endpoint: last_updated date when data was last fetched (Phase 6 scheduler)."""

import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

# Resolve shared config from backend's parent (project root)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LAST_REFRESH_FILE = _PROJECT_ROOT / "shared" / "last_refresh.json"


@router.get("/meta")
def get_meta():
    """Return last_updated date from Phase 6 pipeline (when data was last fetched from URLs)."""
    if not _LAST_REFRESH_FILE.exists():
        return {"last_updated": None, "updated_at_iso": None}
    try:
        data = _LAST_REFRESH_FILE.read_text(encoding="utf-8")
        out = json.loads(data)
        return {
            "last_updated": out.get("last_updated"),
            "updated_at_iso": out.get("updated_at_iso"),
        }
    except Exception:
        return {"last_updated": None, "updated_at_iso": None}
