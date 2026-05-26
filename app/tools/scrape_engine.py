"""
Run category scrapers concurrently (deal-cracker 2 style, no Claude).
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.scraper_config import INTENT_SCRAPER_KEYS, SCRAPING_ENABLED
from app.scrapers import SCRAPER_REGISTRY
from app.tools.intent_parser import SearchIntent
from app.utils.dedup import dedupe_list

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=6)


def scraper_keys_for_intent(intent: SearchIntent) -> list[str]:
    keys: set[str] = set()
    for cat in intent.categories:
        keys.update(INTENT_SCRAPER_KEYS.get(cat, []))
    if intent.store:
        # Named shop: run food + fashion + travel scrapers, filter later
        keys.update(["food", "fashion", "ecommerce", "travel", "entertainment", "delivery"])
    return list(keys) or ["food"]


def _run_scraper(key: str) -> list[dict[str, Any]]:
    fn = SCRAPER_REGISTRY.get(key)
    if not fn:
        return []
    try:
        return fn()
    except Exception as exc:
        logger.error("Scraper %s failed: %s", key, exc)
        return []


async def scrape_for_intent(intent: SearchIntent) -> list[dict[str, Any]]:
    if not SCRAPING_ENABLED:
        return []

    keys = scraper_keys_for_intent(intent)
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(_executor, _run_scraper, key) for key in keys]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    deals: list[dict[str, Any]] = []
    for result in results:
        if isinstance(result, Exception):
            logger.error("Scraper task error: %s", result)
        else:
            deals.extend(result)

    return dedupe_list(deals)
