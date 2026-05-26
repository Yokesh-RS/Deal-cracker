"""E-commerce scrapers."""

from __future__ import annotations

import logging

from app.scrapers.base import abs_url, get_soup, make_deal

logger = logging.getLogger(__name__)


def scrape_argos() -> list[dict]:
    deals: list[dict] = []
    base = "https://www.argos.co.uk"
    soup = get_soup(f"{base}/sale/")
    if not soup:
        return deals
    for item in soup.select("[data-test='component-product-card'], article")[:10]:
        title = item.select_one("[data-test='product-title'], h2, h3")
        price = item.select_one("[data-test='product-price-sale'], .sale-price")
        link = item.select_one("a[href]")
        if not title:
            continue
        deals.append(
            make_deal(
                store="Argos",
                title=title.get_text(strip=True),
                category="shopping",
                url=abs_url(base, link["href"] if link else "/sale"),
                discount=price.get_text(strip=True) if price else "Sale",
                expiry="While stocks last",
            )
        )
    return deals


def scrape_ecommerce() -> list[dict]:
    results: list[dict] = []
    try:
        results.extend(scrape_argos())
    except Exception as exc:
        logger.error("Ecommerce scraper failed: %s", exc)
    return results
