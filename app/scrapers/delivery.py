"""Food delivery scrapers."""

from __future__ import annotations

import logging

from app.scrapers.base import get_soup, make_deal

logger = logging.getLogger(__name__)


def scrape_deliveroo() -> list[dict]:
    deals: list[dict] = []
    url = "https://deliveroo.co.uk/offers"
    soup = get_soup(url)
    if not soup:
        return deals
    for item in soup.select(".offer-card, [data-testid='offer'], article")[:8]:
        title = item.select_one("h2, h3, .offer-title")
        code = item.select_one(".promo-code, .code")
        expiry = item.select_one(".expiry, .valid-until")
        if not title:
            continue
        deals.append(
            make_deal(
                store="Deliveroo",
                title=title.get_text(strip=True),
                category="food",
                url=url,
                expiry=expiry.get_text(strip=True) if expiry else "Limited time",
                coupon=code.get_text(strip=True) if code else None,
            )
        )
    return deals


def scrape_delivery() -> list[dict]:
    try:
        return scrape_deliveroo()
    except Exception as exc:
        logger.error("Delivery scraper failed: %s", exc)
        return []
