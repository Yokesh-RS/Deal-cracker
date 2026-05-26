"""Search static JSON + category scrapers + HotUKDeals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.scraper_config import TOP_DEALS_COUNT
from app.tools.deal_scraper import scrape_live_deals
from app.tools.intent_parser import SearchIntent
from app.tools.scrape_engine import scrape_for_intent
from app.utils.dedup import dedupe_list

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "deals.json"

_deals_cache: Optional[list[dict[str, Any]]] = None

SHOE_WORDS = ("shoe", "shoes", "trainer", "trainers", "sneaker", "sneakers", "footwear")


def load_deals() -> list[dict[str, Any]]:
    global _deals_cache
    if _deals_cache is None:
        with open(DATA_PATH, encoding="utf-8") as f:
            _deals_cache = json.load(f)
    return _deals_cache


def _deal_text(deal: dict[str, Any]) -> str:
    parts = [
        deal.get("store", ""),
        deal.get("title", ""),
        deal.get("offer", ""),
        deal.get("description", ""),
        deal.get("discount", ""),
        " ".join(deal.get("tags") or []),
        deal.get("brand", ""),
    ]
    return " ".join(parts).lower()


def _matches_store(deal: dict[str, Any], store_terms: list[str]) -> bool:
    text = _deal_text(deal)
    return any(term in text for term in store_terms)


def _is_shoe_deal(deal: dict[str, Any]) -> bool:
    return any(w in _deal_text(deal) for w in SHOE_WORDS)


def _matches_student(deal: dict[str, Any]) -> bool:
    tags = [t.lower() for t in deal.get("tags") or []]
    if "student" in tags:
        return True
    return "student" in _deal_text(deal)


def _matches_product(deal: dict[str, Any], product: str) -> bool:
    text = _deal_text(deal)
    if product == "shoes":
        return _is_shoe_deal(deal)
    if product == "coffee":
        return "coffee" in text or deal.get("category") == "coffee"
    return True


def _category_terms(categories: list[str]) -> list[str]:
    mapping = {
        "coffee": ["coffee", "latte", "starbucks", "costa", "cafe", "blacksheep"],
        "burger": ["burger", "mcdonald", "five guys", "kfc", "whopper"],
        "food": ["food", "meal", "lunch", "dinner", "nandos", "restaurant"],
        "pizza": ["pizza"],
        "cinema": ["cinema", "cineworld", "odeon", "vue", "movie"],
        "fashion": ["shoe", "trainer", "sneaker", "fashion"],
        "shopping": ["primark", "shop", "retail", "clothing"],
        "travel": ["airport", "flight", "ryanair", "easyjet", "jet2", "parking", "train"],
    }
    terms: list[str] = []
    for cat in categories:
        terms.extend(mapping.get(cat, [cat]))
    return terms


def _matches_query_keywords(deal: dict[str, Any], intent: SearchIntent) -> bool:
    text = _deal_text(deal)
    if intent.store_terms and not _matches_store(deal, intent.store_terms):
        return False
    if intent.student_only and not _matches_student(deal):
        return False
    if intent.product_filter and not _matches_product(deal, intent.product_filter):
        return False
    if intent.store and not intent.product_filter and _is_shoe_deal(deal):
        if intent.store in ("primark",):
            return False
    live_sources = ("hotukdeals", "myvouchercodes", "scraper")
    if deal.get("source") in live_sources and not intent.store_terms:
        terms = _category_terms(intent.categories)
        if intent.student_only:
            terms.append("student")
        if terms and not any(t in text for t in terms if len(t) > 2):
            return False
    return True


def search_deals(category: str, max_price: Optional[float] = None) -> list[dict[str, Any]]:
    category = category.lower().strip()
    results = [d for d in load_deals() if d.get("category", "").lower() == category]
    if max_price is not None:
        results = [d for d in results if float(d.get("price", 0)) <= max_price]
    return results


def search_by_store(
    store_terms: list[str],
    max_price: Optional[float] = None,
    student_only: bool = False,
    product_filter: Optional[str] = None,
) -> list[dict[str, Any]]:
    results = [d for d in load_deals() if _matches_store(d, store_terms)]
    if student_only:
        results = [d for d in results if _matches_student(d)]
    if product_filter:
        results = [d for d in results if _matches_product(d, product_filter)]
    elif store_terms and any("primark" in t for t in store_terms):
        results = [d for d in results if not _is_shoe_deal(d)]
    if max_price is not None:
        results = [d for d in results if float(d.get("price", 0)) <= max_price]
    return results


def search_multiple_categories(
    categories: list[str],
    max_price: Optional[float] = None,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    combined: list[dict[str, Any]] = []
    for cat in categories:
        for deal in search_deals(cat, max_price=max_price):
            key = f"{deal.get('store')}|{deal.get('title')}"
            if key not in seen:
                seen.add(key)
                combined.append(deal)
    return combined


def _search_static(intent: SearchIntent) -> list[dict[str, Any]]:
    if intent.store and intent.store_terms:
        return search_by_store(
            intent.store_terms,
            max_price=intent.max_price,
            student_only=intent.student_only,
            product_filter=intent.product_filter,
        )
    if intent.product_filter == "shoes":
        results = search_deals("fashion", max_price=intent.max_price)
        return [d for d in results if _matches_product(d, "shoes")]
    return search_multiple_categories(intent.categories, max_price=intent.max_price)


async def search_all_async(intent: SearchIntent) -> list[dict[str, Any]]:
    """Static JSON + retailer scrapers + HotUKDeals."""
    static = _search_static(intent)

    scraped: list[dict[str, Any]] = []
    try:
        scraped = await scrape_for_intent(intent)
        scraped = [d for d in scraped if _matches_query_keywords(d, intent)]
    except Exception:
        scraped = []

    aggregator: list[dict[str, Any]] = []
    try:
        aggregator = scrape_live_deals(intent.scrape_query, store=intent.store)
        aggregator = [d for d in aggregator if _matches_query_keywords(d, intent)]
    except Exception:
        aggregator = []

    merged = dedupe_list(static + scraped + aggregator)

    if intent.store and intent.store_terms:
        return [d for d in merged if _matches_store(d, intent.store_terms)]

    if len(static) >= TOP_DEALS_COUNT and not intent.store:
        static_only = dedupe_list(static)
        if len(static_only) >= TOP_DEALS_COUNT:
            return static_only

    return merged


def search_all(intent: SearchIntent) -> list[dict[str, Any]]:
    """Sync wrapper (tests / FastAPI)."""
    import asyncio

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(search_all_async(intent))

    # Called from running loop — use static + sync aggregator only
    static = _search_static(intent)
    aggregator: list[dict[str, Any]] = []
    try:
        aggregator = scrape_live_deals(intent.scrape_query, store=intent.store)
        aggregator = [d for d in aggregator if _matches_query_keywords(d, intent)]
    except Exception:
        pass
    merged = dedupe_list(static + aggregator)
    if intent.store and intent.store_terms:
        return [d for d in merged if _matches_store(d, intent.store_terms)]
    return merged
