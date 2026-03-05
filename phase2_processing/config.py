"""Phase 2: Processing configuration."""

from pathlib import Path
import sys

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.config import PHASE1_OUTPUT, PHASE2_OUTPUT  # type: ignore  # noqa: E402

# Input directory: Phase 1 output (JSON docs per fund)
INPUT_DIR = PHASE1_OUTPUT

# Output directory: structured chunks for embeddings
OUTPUT_DIR = PHASE2_OUTPUT

# Output directory: one JSON per fund (for viewing/verification)
OUTPUT_DIR_FUND_WISE = PROJECT_ROOT / "phase2_processing" / "output" / "fund_wise"

# Chunking configuration
CHUNK_MAX_CHARS = 1200
CHUNK_OVERLAP_CHARS = 200

