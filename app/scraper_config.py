"""Scraper settings (no API keys — local agent only)."""

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
CACHE_FILE = DATA_DIR / "scraped_cache.json"
SEEN_FILE = DATA_DIR / "seen_deals.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

SCRAPING_ENABLED = os.getenv("SCRAPING_ENABLED", "true").lower() != "false"
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "10"))
TOP_DEALS_COUNT = int(os.getenv("TOP_DEALS_COUNT", "3"))

SCRAPER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

# Intent categories → scraper modules to run
INTENT_SCRAPER_KEYS: dict[str, list[str]] = {
    "coffee": ["food"],
    "burger": ["food", "delivery"],
    "food": ["food", "delivery", "grocery"],
    "pizza": ["food", "delivery"],
    "cinema": ["entertainment"],
    "shopping": ["fashion", "ecommerce"],
    "fashion": ["fashion", "ecommerce"],
    "travel": ["travel"],
}
