"""Grocery scrapers."""

from __future__ import annotations

import logging

from app.scrapers.base import abs_url, get_soup, make_deal

logger = logging.getLogger(__name__)


def scrape_tesco() -> list[dict]:
    deals: list[dict] = []
    base = "https://www.tesco.com"
    soup = get_soup(f"{base}/groceries/en-GB/promotions")
    if not soup:
        return deals
    for item in soup.select(".product-list--list-item, .tile-content, article")[:10]:
        title = item.select_one("h3, .product-tile--title, a")
        price = item.select_one(".offer-text, .clubcard-price")
        link = item.select_one("a[href]")
        if not title:
            continue
        deals.append(
            make_deal(
                store="Tesco",
                title=title.get_text(strip=True),
                category="food",
                url=abs_url(base, link["href"] if link else "/groceries"),
                discount=price.get_text(strip=True) if price else "Clubcard price",
                expiry="While stocks last",
            )
        )
    return deals


def scrape_grocery() -> list[dict]:
    try:
        return scrape_tesco()
    except Exception as exc:
        logger.error("Grocery scraper failed: %s", exc)
        return []
