"""Entertainment scrapers."""

from __future__ import annotations

import logging

from app.scrapers.base import abs_url, get_soup, make_deal

logger = logging.getLogger(__name__)


def scrape_cineworld() -> list[dict]:
    deals: list[dict] = []
    base = "https://www.cineworld.co.uk"
    soup = get_soup(f"{base}/offers")
    if not soup:
        return deals
    for item in soup.select(".offer, .promo-card, .deal-card, article")[:8]:
        title = item.select_one("h2, h3")
        desc = item.select_one("p")
        link = item.select_one("a[href]")
        if not title:
            continue
        deals.append(
            make_deal(
                store="Cineworld",
                title=title.get_text(strip=True),
                category="cinema",
                url=abs_url(base, link["href"] if link else "/offers"),
                description=desc.get_text(strip=True) if desc else "",
                expiry="See website",
            )
        )
    return deals


def scrape_odeon() -> list[dict]:
    deals: list[dict] = []
    base = "https://www.odeon.co.uk"
    soup = get_soup(f"{base}/offers/")
    if not soup:
        return deals
    for item in soup.select(".offer-card, .promo, article")[:8]:
        title = item.select_one("h2, h3, .offer-title")
        desc = item.select_one("p")
        link = item.select_one("a[href]")
        if not title:
            continue
        deals.append(
            make_deal(
                store="Odeon",
                title=title.get_text(strip=True),
                category="cinema",
                url=abs_url(base, link["href"] if link else "/offers"),
                description=desc.get_text(strip=True) if desc else "",
                expiry="See website",
            )
        )
    return deals


def scrape_entertainment() -> list[dict]:
    results: list[dict] = []
    for fn in (scrape_cineworld, scrape_odeon):
        try:
            results.extend(fn())
        except Exception as exc:
            logger.error("Entertainment scraper %s failed: %s", fn.__name__, exc)
    return results
