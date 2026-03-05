"""Phase 1: Data ingestion configuration."""

from pathlib import Path

# Import shared fund URLs; extend with phase-specific settings
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.config import FUND_URLS, PROJECT_ROOT

# Output directory for raw scraped data
OUTPUT_DIR = PROJECT_ROOT / "phase1_data_ingestion" / "output"

# Playwright / scraping
PAGE_LOAD_TIMEOUT_MS = 60_000
NAVIGATION_TIMEOUT_MS = 45_000
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2
DELAY_BETWEEN_REQUESTS_SECONDS = 2  # Rate limiting

# Optional: CSS selectors for main content (IndMoney structure; adjust after inspecting pages)
MAIN_CONTENT_SELECTOR = "main, [role='main'], .main-content, #__next"
BODY_SELECTOR = "body"
