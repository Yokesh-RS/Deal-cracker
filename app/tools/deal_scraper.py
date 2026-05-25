"""
Live deal scraping from public UK deal pages.

Sources:
  - HotUKDeals tag/search pages
  - MyVoucherCodes brand discount pages (fallback)

Results are merged with static JSON in deal_search.search_all().
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Optional
from urllib.parse import quote_plus

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 12
CACHE_TTL_SECONDS = 900  # 15 minutes

_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def _scraping_enabled() -> bool:
    return os.getenv("SCRAPING_ENABLED", "true").lower() != "false"


def _fetch(url: str) -> str:
    resp = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.text


def _slug_to_title(slug: str) -> str:
    title = slug.replace("-", " ")
    title = re.sub(r"\bps(\d+)\b", r"£\1.", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip()
    return title[:120]


def _parse_price_from_slug(slug: str) -> float:
    m = re.search(r"ps(\d+)(?:p(\d+))?", slug, re.I)
    if m:
        pounds = int(m.group(1))
        pence = int(m.group(2) or 0)
        return pounds + pence / 100
    m = re.search(r"£\s*(\d+(?:\.\d+)?)", slug)
    if m:
        return float(m.group(1))
    return 0.0


def _parse_hotukdeals_html(html: str, query: str) -> list[dict[str, Any]]:
    deals: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Embedded thread JSON in Vue props (richest data)
    for block in re.finditer(
        r'"thread":\{(.*?)\}\s*\}\s*\'',
        html,
        re.DOTALL,
    ):
        chunk = block.group(1)
        title_m = re.search(r'"title":"((?:[^"\\]|\\.)*)"', chunk)
        price_m = re.search(r'"price":(\d+(?:\.\d+)?)', chunk)
        slug_m = re.search(r'"titleSlug":"([^"]+)"', chunk)
        if not title_m:
            continue
        try:
            title = json.loads(f'"{title_m.group(1)}"')
        except json.JSONDecodeError:
            title = title_m.group(1).replace("\\u00a3", "£")

        slug = slug_m.group(1) if slug_m else ""
        price = float(price_m.group(1)) if price_m else _parse_price_from_slug(slug)
        url = f"https://www.hotukdeals.com/deals/{slug}" if slug else ""
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        store = _guess_store_from_title(title, query)
        deals.append(
            {
                "store": store,
                "title": title[:100],
                "price": price,
                "distance": 0.0,
                "offer": "Live deal from HotUKDeals",
                "category": _guess_category(title, query),
                "url": url,
                "source": "hotukdeals",
                "tags": _guess_tags(title),
            }
        )

    # Fallback: thread-link anchors
    if len(deals) < 3:
        for title, url in re.findall(
            r'class="[^"]*thread-link[^"]*"[^>]*title="([^"]+)"[^>]*href="(https://www\.hotukdeals\.com/deals/[^"]+)"',
            html,
        ):
            if url in seen_urls:
                continue
            seen_urls.add(url)
            slug = url.rstrip("/").split("/")[-1]
            deals.append(
                {
                    "store": _guess_store_from_title(title, query),
                    "title": title[:100],
                    "price": _parse_price_from_slug(slug),
                    "distance": 0.0,
                    "offer": "Live deal from HotUKDeals",
                    "category": _guess_category(title, query),
                    "url": url,
                    "source": "hotukdeals",
                    "tags": _guess_tags(title),
                }
            )

    return deals[:15]


def _parse_myvouchercodes_html(html: str, brand: str) -> list[dict[str, Any]]:
    deals: list[dict[str, Any]] = []
    brand_title = brand.replace(".com", "").title()

    for title, code in re.findall(
        r'<h[23][^>]*>([^<]*(?:' + re.escape(brand_title[:6]) + r')[^<]*)</h',
        html,
        re.I,
    ):
        deals.append(
            {
                "store": brand_title,
                "title": title.strip()[:80],
                "price": 0.0,
                "distance": 0.0,
                "offer": "Voucher / discount code — see link",
                "category": "shopping",
                "url": f"https://www.myvouchercodes.co.uk/discount-codes/{brand}",
                "source": "myvouchercodes",
                "tags": [],
            }
        )

    # Generic “X% off” lines
    for pct, desc in re.findall(
        r"(\d+)%\s*off[^<]{0,80}",
        html,
        re.I,
    )[:5]:
        deals.append(
            {
                "store": brand_title,
                "title": f"{pct}% off — {desc.strip()[:60]}",
                "price": 0.0,
                "distance": 0.0,
                "offer": f"{pct}% off",
                "category": "shopping",
                "url": f"https://www.myvouchercodes.co.uk/discount-codes/{brand}",
                "source": "myvouchercodes",
                "tags": [],
            }
        )

    return deals[:5]


def _guess_store_from_title(title: str, query: str) -> str:
    lower = title.lower()
    for word in query.lower().split():
        if len(word) > 3 and word in lower:
            return word.title()
    if "blacksheep" in lower or "black sheep" in lower:
        return "Blacksheep Coffee"
    if "primark" in lower:
        return "Primark"
    if "starbucks" in lower:
        return "Starbucks"
    if "airport" in lower or "flight" in lower:
        return "Travel"
    return "HotUKDeals"


def _guess_category(title: str, query: str) -> str:
    text = (title + " " + query).lower()
    if any(w in text for w in ("airport", "flight", "ryanair", "easyjet", "jet2", "train")):
        return "travel"
    if "student" in text:
        return "shopping"
    if "primark" in text:
        return "shopping"
    if "starbucks" in text or "coffee" in text:
        return "coffee"
    if "cinema" in text or "odeon" in text:
        return "cinema"
    return "shopping"


def _guess_tags(title: str) -> list[str]:
    lower = title.lower()
    tags: list[str] = []
    if "student" in lower:
        tags.append("student")
    if any(w in lower for w in ("airport", "flight")):
        tags.append("travel")
    return tags


def scrape_hotukdeals(query: str) -> list[dict[str, Any]]:
    """Scrape HotUKDeals tag page for a keyword (e.g. starbucks, primark, airport)."""
    if not _scraping_enabled() or not query.strip():
        return []

    tag = query.lower().strip().replace(" ", "-")
    tag = re.sub(r"[^a-z0-9\-]", "", tag)

    # Map common intents to working HotUKDeals tags
    tag_aliases = {
        "glasgow-airport-flight": "travel",
        "travel": "travel",
        "airport": "travel",
        "flight": "travel",
        "burger": "restaurant",
        "food": "restaurant",
        "student-starbucks": "starbucks",
        "student": "student",
        "blacksheep": "coffee",
        "blacksheep-coffee": "coffee",
    }
    primary_tag = tag_aliases.get(tag, tag.split("-")[0] if tag else "deals")

    urls = [
        f"https://www.hotukdeals.com/tag/{primary_tag}",
        f"https://www.hotukdeals.com/tag/{tag}" if tag != primary_tag else "",
    ]
    urls = [u for u in urls if u]

    all_deals: list[dict[str, Any]] = []
    seen: set[str] = set()
    for url in urls:
        try:
            html = _fetch(url)
            for d in _parse_hotukdeals_html(html, query):
                key = d.get("url") or d.get("title")
                if key not in seen:
                    seen.add(key)
                    all_deals.append(d)
        except requests.RequestException:
            continue
        if len(all_deals) >= 5:
            break
    return all_deals


def scrape_myvouchercodes(brand: str) -> list[dict[str, Any]]:
    """Scrape brand voucher page on MyVoucherCodes."""
    if not _scraping_enabled():
        return []
    slug = brand.lower().replace(" ", "")
    if not slug.endswith(".com"):
        slug = f"{slug}.com"
    url = f"https://www.myvouchercodes.co.uk/discount-codes/{slug}"
    try:
        html = _fetch(url)
        return _parse_myvouchercodes_html(html, slug)
    except requests.RequestException:
        return []


def scrape_live_deals(query: str, store: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Fetch live deals with short-lived cache.
    Uses HotUKDeals + optional MyVoucherCodes for known brands.
    """
    cache_key = f"{query}|{store or ''}"
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return data

    results = scrape_hotukdeals(query)
    if store:
        brand_slugs = {
            "starbucks": "starbucks.com",
            "primark": "primark.com",
            "costa": "costa.co.uk",
        }
        if store in brand_slugs:
            results = results + scrape_myvouchercodes(brand_slugs[store])

    _cache[cache_key] = (now, results)
    return results
