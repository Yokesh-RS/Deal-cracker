"""Search static + live deals data with store, student, and product filters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.tools.deal_scraper import scrape_live_deals
from app.tools.intent_parser import SearchIntent

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
    text = _deal_text(deal)
    return "student" in text


def _matches_product(deal: dict[str, Any], product: str) -> bool:
    text = _deal_text(deal)
    if product == "shoes":
        return _is_shoe_deal(deal)
    if product == "coffee":
        return "coffee" in text or deal.get("category") == "coffee"
    return True


def _category_terms(categories: list[str]) -> list[str]:
    mapping = {
        "coffee": ["coffee", "latte", "starbucks", "costa", "cafe"],
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
    """Relevance filter for scraped deals."""
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
    # Scraped deals must mention the requested topic (avoids random HotUKDeals tag noise)
    if deal.get("source") in ("hotukdeals", "myvouchercodes"):
        terms = _category_terms(intent.categories) + intent.store_terms
        if intent.student_only:
            terms.append("student")
        if terms and not any(t in text for t in terms if len(t) > 2):
            return False
    return True


def search_deals(
    category: str,
    max_price: Optional[float] = None,
) -> list[dict[str, Any]]:
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


def _dedupe(deals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for d in deals:
        key = f"{d.get('store')}|{d.get('title')}|{d.get('url', '')}"
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def search_all(intent: SearchIntent) -> list[dict[str, Any]]:
    """
    Merge static database + live scraped deals for this intent.
    """
    static: list[dict[str, Any]] = []

    if intent.store and intent.store_terms:
        static = search_by_store(
            intent.store_terms,
            max_price=intent.max_price,
            student_only=intent.student_only,
            product_filter=intent.product_filter,
        )
    elif intent.product_filter == "shoes":
        static = search_deals("fashion", max_price=intent.max_price)
        static = [d for d in static if _matches_product(d, "shoes")]
    else:
        static = search_multiple_categories(intent.categories, max_price=intent.max_price)

    live: list[dict[str, Any]] = []
    try:
        live = scrape_live_deals(intent.scrape_query, store=intent.store)
        live = [d for d in live if _matches_query_keywords(d, intent)]
    except Exception:
        live = []

    # Named store: never mix in unrelated category deals (e.g. Starbucks for Blacksheep)
    if intent.store and intent.store_terms:
        merged = _dedupe(static + live)
        merged = [d for d in merged if _matches_store(d, intent.store_terms)]
        return merged

    # Prefer good static matches; only add live when static is thin
    if len(static) >= 3:
        merged = _dedupe(static)
    else:
        merged = _dedupe(static + live)

    return merged
