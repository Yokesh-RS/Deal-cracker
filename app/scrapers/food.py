"""Food & coffee scrapers."""

from __future__ import annotations

import logging

from app.scrapers.base import abs_url, get_soup, make_deal

logger = logging.getLogger(__name__)


def scrape_mcdonalds() -> list[dict]:
    deals: list[dict] = []
    base = "https://www.mcdonalds.com"
    soup = get_soup(f"{base}/gb/en-gb/offers.html")
    if not soup:
        return deals
    for item in soup.select(".offer-card, [data-module='offers'], article")[:10]:
        title = item.select_one("h2, h3, .offer-title, .card-title")
        desc = item.select_one("p, .offer-desc")
        link = item.select_one("a[href]")
        if not title:
            continue
        deals.append(
            make_deal(
                store="McDonald's",
                title=title.get_text(strip=True),
                category="food",
                url=abs_url(base, link["href"] if link else "/gb/en-gb/offers.html"),
                description=desc.get_text(strip=True) if desc else "",
                expiry="Limited time",
            )
        )
    return deals


def scrape_starbucks() -> list[dict]:
    deals: list[dict] = []
    url = "https://www.starbucks.co.uk/rewards"
    soup = get_soup(url)
    if not soup:
        return deals
    for item in soup.select(".reward-card, .offer, .promo, article")[:10]:
        title = item.select_one("h2, h3, .title")
        desc = item.select_one("p")
        if not title:
            continue
        text = (title.get_text(strip=True) + " " + (desc.get_text(strip=True) if desc else "")).lower()
        tags = ["student"] if "student" in text else []
        deal = make_deal(
            store="Starbucks",
            title=title.get_text(strip=True),
            category="coffee",
            url=url,
            description=desc.get_text(strip=True) if desc else "",
            expiry="See app",
        )
        deal["tags"] = tags
        deals.append(deal)
    return deals


def scrape_blacksheep() -> list[dict]:
    deals: list[dict] = []
    url = "https://blacksheepcoffee.co.uk"
    soup = get_soup(url)
    if not soup:
        return deals
    for item in soup.select("article, .card, .promo, h2, h3")[:8]:
        if item.name in ("h2", "h3"):
            title_text = item.get_text(strip=True)
            if len(title_text) < 5:
                continue
            deals.append(
                make_deal(
                    store="Blacksheep Coffee",
                    title=title_text[:80],
                    category="coffee",
                    url=f"{url}/pages/locations",
                    description="Check site for current offers",
                    expiry="See website",
                )
            )
    if not deals:
        deals.append(
            make_deal(
                store="Blacksheep Coffee",
                title="App & in-store offers",
                category="coffee",
                url=f"{url}/pages/app",
                description="Download the Blacksheep app for discounts",
                expiry="See website",
            )
        )
    return deals


def scrape_food() -> list[dict]:
    results: list[dict] = []
    for fn in (scrape_mcdonalds, scrape_starbucks, scrape_blacksheep):
        try:
            results.extend(fn())
        except Exception as exc:
            logger.error("Food scraper %s failed: %s", fn.__name__, exc)
    return results
