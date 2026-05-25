"""
Parse user messages into search intent.

Fixes false matches (e.g. Primark → all shoe shops) by prioritising
explicit store names and product keywords over broad categories.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Brand → search terms (store field / scrape query)
KNOWN_STORES: dict[str, list[str]] = {
    "blacksheep coffee": ["blacksheep", "black sheep", "blacksheep coffee"],
    "primark": ["primark"],
    "starbucks": ["starbucks"],
    "costa": ["costa"],
    "pret": ["pret a manger", "pret"],
    "caffe nero": ["caffe nero", "nero"],
    "greggs": ["greggs"],
    "mcdonalds": ["mcdonald", "mcdonalds"],
    "nandos": ["nando"],
    "pizza express": ["pizza express"],
    "cineworld": ["cineworld"],
    "odeon": ["odeon"],
    "vue": ["vue glasgow", "vue cinema"],
    "sports direct": ["sports direct"],
    "jd sports": ["jd sports"],
    "ryanair": ["ryanair"],
    "easyjet": ["easyjet"],
    "jet2": ["jet2"],
    "glasgow airport": ["glasgow airport", "gla airport"],
}

# Chains — used to avoid treating "starbucks coffee" as an unknown boutique
KNOWN_CHAIN_TERMS = frozenset(
    {
        "starbucks", "costa", "greggs", "mcdonald", "mcdonalds", "pret",
        "nero", "caffe nero", "burger king", "kfc", "subway", "dominos",
    }
)

# Product words — only narrow results when explicitly mentioned
PRODUCT_KEYWORDS: dict[str, list[str]] = {
    "shoes": ["shoe", "shoes", "trainer", "trainers", "sneaker", "sneakers", "footwear"],
    "burger": ["burger", "burgers"],
    "pizza": ["pizza"],
}

# Generic coffee requests (not a named café)
GENERIC_COFFEE_PHRASES = frozenset(
    {
        "coffee",
        "i want coffee",
        "need coffee",
        "any coffee",
        "cheap coffee",
        "coffee nearby",
        "coffee deals",
        "want coffee",
    }
)

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "coffee": ["coffee", "latte", "espresso", "cappuccino", "americano", "caffeine"],
    "pizza": ["pizza", "pizzeria"],
    "cinema": ["cinema", "movie", "film", "odeon", "cineworld", "screening", "movie ticket"],
    "burger": ["burger", "burgers", "whopper", "cheeseburger"],
    "fashion": ["fashion", "clothes", "clothing", "outfit"],
    "shopping": ["shopping", "retail"],
    "food": ["dinner", "lunch", "food", "meal", "eat", "hungry", "takeaway"],
    "travel": [
        "airport",
        "flight",
        "flights",
        "fly",
        "airline",
        "holiday",
        "travel",
        "glasgow airport",
        "gla",
        "ryanair",
        "easyjet",
        "jet2",
        "train to airport",
        "bus to airport",
    ],
}

CATEGORY_HEADLINES: dict[str, str] = {
    "coffee": "🔥 Best coffee deals nearby:",
    "burger": "🔥 Best burger deals nearby:",
    "food": "🔥 Best food deals nearby:",
    "pizza": "🔥 Best pizza deals nearby:",
    "cinema": "🔥 Best cinema deals nearby:",
    "shopping": "🔥 Best shopping deals nearby:",
    "fashion": "🔥 Best fashion deals nearby:",
    "travel": "✈️ Best travel & airport deals:",
}


@dataclass
class SearchIntent:
    raw_message: str
    categories: list[str] = field(default_factory=list)
    store: Optional[str] = None  # canonical store key, e.g. "primark"
    store_terms: list[str] = field(default_factory=list)
    product_filter: Optional[str] = None  # e.g. "shoes"
    student_only: bool = False
    max_price: Optional[float] = None
    scrape_query: str = ""
    headline: str = "🔥 Best deals nearby:"


def parse_max_price(message: str) -> Optional[float]:
    patterns = [
        r"(?:under|below|less than|max|up to)\s*£?\s*(\d+(?:\.\d+)?)",
        r"£\s*(\d+(?:\.\d+)?)\s*(?:or less|max)",
    ]
    lower = message.lower()
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            return float(match.group(1))
    return None


def detect_store(message: str) -> tuple[Optional[str], list[str]]:
    lower = message.lower()
    # Longer store names first (pizza express before pizza)
    for store, terms in sorted(KNOWN_STORES.items(), key=lambda x: -len(x[0])):
        if any(t in lower for t in terms):
            return store, terms
    return detect_dynamic_store(message)


def detect_dynamic_store(message: str) -> tuple[Optional[str], list[str]]:
    """
    Extract boutique / indie brands from phrases like 'blacksheep coffee'
    or 'deals at wagamama' when not in KNOWN_STORES.
    """
    lower = message.lower().strip()
    if lower in GENERIC_COFFEE_PHRASES:
        return None, []

    patterns = [
        r"([a-z][a-z0-9\s&'-]{2,40}?)\s+coffee\b",
        r"\bcoffee\s+(?:at|from|in|@)\s+([a-z][a-z0-9\s&'-]{2,40})",
        r"(?:offers?|deals?)\s+(?:at|on|for|from)\s+([a-z][a-z0-9\s&'-]{2,40})",
        r"(?:anything|any)\s+(?:at|from)\s+([a-z][a-z0-9\s&'-]{2,40})",
    ]
    for pattern in patterns:
        match = re.search(pattern, lower)
        if not match:
            continue
        brand = match.group(1).strip()
        brand = re.sub(r"\s+(offers?|deals?|nearby|please)$", "", brand).strip()
        if len(brand) < 3:
            continue
        if any(chain in brand for chain in KNOWN_CHAIN_TERMS):
            continue
        if brand in ("the", "a", "an", "some", "any"):
            continue
        terms = [brand]
        if " " in brand:
            terms.append(brand.replace(" ", ""))
        return brand, terms
    return None, []


def detect_product_filter(message: str) -> Optional[str]:
    lower = message.lower()
    for product, terms in PRODUCT_KEYWORDS.items():
        if any(t in lower for t in terms):
            return product
    return None


def detect_categories(message: str, store: Optional[str], product: Optional[str]) -> list[str]:
    lower = message.lower()

    # Travel beats vague "ticket" / cinema overlap
    if any(
        w in lower
        for w in (
            "airport",
            "flight",
            "flights",
            "fly ",
            "airline",
            "ryanair",
            "easyjet",
            "jet2",
            "glasgow airport",
        )
    ):
        return ["travel"]

    matched: list[str] = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            matched.append(category)

    # Store-specific query without product → don't pull entire fashion/shopping
    if store:
        store_category_map = {
            "primark": "shopping",
            "blacksheep coffee": "coffee",
            "starbucks": "coffee",
            "costa": "coffee",
            "pret": "coffee",
            "caffe nero": "coffee",
            "greggs": "food",
            "mcdonalds": "burger",
            "nandos": "food",
            "cineworld": "cinema",
            "odeon": "cinema",
            "vue": "cinema",
            "sports direct": "fashion",
            "jd sports": "fashion",
            "ryanair": "travel",
            "easyjet": "travel",
            "jet2": "travel",
            "glasgow airport": "travel",
        }
        primary = store_category_map.get(store)
        if product == "shoes":
            return ["fashion"]
        if primary and primary not in matched:
            matched.insert(0, primary)
        # Primark / Starbucks etc.: prefer store filter only
        if not product:
            return matched[:1] if matched else ([primary] if primary else ["shopping"])

    if product == "shoes":
        return ["fashion"]

    if not matched:
        if any(w in lower for w in ("cheap", "deal", "offer", "nearby", "tonight")):
            return ["food", "burger"]
        return ["food"]

    if "fashion" in matched and "shopping" in matched and product != "shoes":
        matched = [c for c in matched if c != "fashion"] or matched

    return matched


def build_scrape_query(intent: SearchIntent) -> str:
    parts: list[str] = []
    if intent.store_terms:
        parts.extend(intent.store_terms[:2])
    elif intent.categories:
        parts.append(intent.categories[0])
    if intent.student_only:
        parts.append("student")
    if intent.product_filter == "shoes":
        parts.append("shoes")
    if "travel" in intent.categories and not intent.store:
        parts.extend(["glasgow", "airport", "flight"])
    return " ".join(parts) or intent.raw_message


def build_headline(intent: SearchIntent) -> str:
    if intent.student_only and intent.store:
        name = intent.store.title()
        return f"🎓 Best student offers at {name}:"
    if intent.store:
        name = intent.store.title()
        if "Coffee" not in name and intent.categories == ["coffee"]:
            name += " Coffee"
        return f"🔥 Best {name} offers:"
    if intent.categories:
        return CATEGORY_HEADLINES.get(
            intent.categories[0],
            "🔥 Best deals nearby:",
        )
    return "🔥 Best deals nearby:"


def parse_intent(message: str) -> SearchIntent:
    message = (message or "").strip()
    lower = message.lower()
    store, store_terms = detect_store(message)
    product = detect_product_filter(message)
    # "blacksheep coffee" is a shop name, not a product filter
    if store and product == "coffee":
        product = None
    student_only = "student" in lower
    categories = detect_categories(message, store, product)
    max_price = parse_max_price(message)

    intent = SearchIntent(
        raw_message=message,
        categories=categories,
        store=store,
        store_terms=store_terms,
        product_filter=product,
        student_only=student_only,
        max_price=max_price,
    )
    intent.scrape_query = build_scrape_query(intent)
    intent.headline = build_headline(intent)
    return intent
