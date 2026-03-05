"""Playwright-based scraper for IndMoney mutual fund pages."""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from .config import (
    DELAY_BETWEEN_REQUESTS_SECONDS,
    FUND_URLS,
    MAIN_CONTENT_SELECTOR,
    NAVIGATION_TIMEOUT_MS,
    OUTPUT_DIR,
    PAGE_LOAD_TIMEOUT_MS,
    RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _extract_sections(page) -> dict:
    """Extract optional section text from the page for later parsing in Phase 2."""
    sections = {
        "overview": "",
        "performance": "",
        "asset_allocation": "",
        "sector_allocation": "",
        "holdings": "",
        "about": "",
        "faq": "",
    }
    try:
        # Try to get main content as a single block (fallback for Phase 2 to parse)
        for selector in MAIN_CONTENT_SELECTOR.split(", "):
            el = page.query_selector(selector.strip())
            if el:
                sections["overview"] = el.inner_text()[:50000] or ""  # cap size
                break
        if not sections["overview"]:
            body = page.query_selector("body")
            if body:
                sections["overview"] = body.inner_text()[:50000] or ""
    except Exception as e:
        logger.warning("Section extraction failed: %s", e)
    return sections


def scrape_fund(fund: dict, output_dir: Path) -> tuple[bool, str]:
    """
    Scrape one fund URL with Playwright. Returns (success, message).
    Saves raw HTML and extracted_sections to output_dir.
    """
    fund_id = fund["id"]
    fund_name = fund["name"]
    url = fund["url"]

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ),
                )
                context.set_default_timeout(PAGE_LOAD_TIMEOUT_MS)
                page = context.new_page()
                page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)

                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT_MS)

                raw_html = page.content()
                extracted_sections = _extract_sections(page)

                browser.close()

            scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            payload = {
                "fund_id": fund_id,
                "fund_name": fund_name,
                "url": url,
                "scraped_at": scraped_at,
                "raw_html": raw_html,
                "extracted_sections": extracted_sections,
            }

            output_dir.mkdir(parents=True, exist_ok=True)
            out_file = output_dir / f"{fund_id}_{timestamp}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            logger.info("Scraped fund_id=%s -> %s", fund_id, out_file.name)
            return True, str(out_file)

        except PlaywrightTimeout as e:
            logger.warning("Timeout (attempt %s/%s) for %s: %s", attempt, RETRY_ATTEMPTS, url, e)
        except Exception as e:
            logger.warning("Error (attempt %s/%s) for %s: %s", attempt, RETRY_ATTEMPTS, url, e)

        if attempt < RETRY_ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS)

    logger.error("Failed after %s attempts: %s", RETRY_ATTEMPTS, url)
    return False, url


def run_scraper(output_dir: Path | None = None) -> dict:
    """
    Scrape all FUND_URLs. Returns summary with success count and failed URLs.
    """
    output_dir = output_dir or OUTPUT_DIR
    results = {"success": 0, "failed": 0, "files": [], "failed_urls": []}

    for i, fund in enumerate(FUND_URLS):
        if i > 0:
            time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)
        ok, msg = scrape_fund(fund, output_dir)
        if ok:
            results["success"] += 1
            results["files"].append(msg)
        else:
            results["failed"] += 1
            results["failed_urls"].append(msg)
    return results
