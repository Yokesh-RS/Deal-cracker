"""Travel scrapers."""

from __future__ import annotations

import logging

from app.scrapers.base import abs_url, get_soup, make_deal

logger = logging.getLogger(__name__)


def scrape_trainline() -> list[dict]:
    deals: list[dict] = []
    base = "https://www.thetrainline.com"
    soup = get_soup(f"{base}/information/promotions")
    if not soup:
        return deals
    for item in soup.select("article, .promo-card, .promotion")[:8]:
        title = item.select_one("h2, h3")
        desc = item.select_one("p")
        link = item.select_one("a[href]")
        if not title:
            continue
        deals.append(
            make_deal(
                store="Trainline",
                title=title.get_text(strip=True),
                category="travel",
                url=abs_url(base, link["href"] if link else "/"),
                description=desc.get_text(strip=True) if desc else "",
                expiry="See website",
            )
        )
    return deals


def scrape_glasgow_airport() -> list[dict]:
    deals: list[dict] = []
    url = "https://www.glasgowairport.com/parking"
    soup = get_soup(url)
    if not soup:
        return deals
    for item in soup.select("article, .card, h2, h3")[:6]:
        if item.name in ("h2", "h3"):
            t = item.get_text(strip=True)
            if "park" in t.lower() or "offer" in t.lower() or len(t) > 8:
                deals.append(
                    make_deal(
                        store="Glasgow Airport",
                        title=t[:80],
                        category="travel",
                        url=url,
                        description="Airport parking & transport",
                        expiry="See website",
                    )
                )
    if not deals:
        deals.append(
            make_deal(
                store="Glasgow Airport",
                title="Parking & transport offers",
                category="travel",
                url=url,
                description="Book parking and check transport options",
                expiry="See website",
            )
        )
    return deals


def scrape_travel() -> list[dict]:
    results: list[dict] = []
    for fn in (scrape_trainline, scrape_glasgow_airport):
        try:
            results.extend(fn())
        except Exception as exc:
            logger.error("Travel scraper %s failed: %s", fn.__name__, exc)
    return results
