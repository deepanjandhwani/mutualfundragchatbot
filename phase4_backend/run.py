"""Run Phase 4 backend (uvicorn). Load .env for GROQ_API_KEY."""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Load .env so GROQ_API_KEY is available
try:
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

import uvicorn
from phase4_backend.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
