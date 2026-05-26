"""Fashion scrapers."""

from __future__ import annotations

import logging

from app.scrapers.base import abs_url, get_soup, make_deal

logger = logging.getLogger(__name__)


def scrape_primark() -> list[dict]:
    deals: list[dict] = []
    base = "https://www.primark.com"
    soup = get_soup(f"{base}/en-gb")
    if not soup:
        return deals
    for item in soup.select("article, .product, .tile, a[href*='products']")[:12]:
        title = item.select_one("h2, h3, .title, span")
        link = item if item.name == "a" else item.select_one("a[href]")
        if not title:
            continue
        title_text = title.get_text(strip=True)
        if len(title_text) < 4 or "cookie" in title_text.lower():
            continue
        deals.append(
            make_deal(
                store="Primark",
                title=title_text[:80],
                category="shopping",
                url=abs_url(base, link["href"] if link else "/en-gb"),
                description="In-store and online offers",
                expiry="While stocks last",
            )
        )
    if not deals:
        deals.append(
            make_deal(
                store="Primark Argyle Street",
                title="Glasgow store — latest offers",
                category="shopping",
                url=f"{base}/en-gb/stores/glasgow/argyle-street",
                description="Visit store page for current promotions",
                expiry="See website",
            )
        )
    return deals


def scrape_hm() -> list[dict]:
    deals: list[dict] = []
    base = "https://www2.hm.com"
    soup = get_soup(f"{base}/en_gb/sale/women.html")
    if not soup:
        return deals
    for item in soup.select(".product-item, article")[:12]:
        title = item.select_one(".item-heading, h2, h3")
        price = item.select_one(".sale, .price-sale, .price")
        link = item.select_one("a[href]")
        if not title:
            continue
        deals.append(
            make_deal(
                store="H&M",
                title=title.get_text(strip=True),
                category="fashion",
                url=abs_url(base, link["href"] if link else "/en_gb/sale"),
                discount=price.get_text(strip=True) if price else "Sale",
                expiry="While stocks last",
            )
        )
    return deals


def scrape_asos() -> list[dict]:
    deals: list[dict] = []
    base = "https://www.asos.com"
    soup = get_soup(f"{base}/women/sale/cat/?cid=8409")
    if not soup:
        return deals
    for item in soup.select("article[data-auto-id='productTile'], article")[:12]:
        title = item.select_one("[data-auto-id='productTileDescription'], h2, h3")
        price = item.select_one("[data-auto-id='productTileReducedPrice'], .sale-price")
        link = item.select_one("a[href]")
        if not title:
            continue
        deals.append(
            make_deal(
                store="ASOS",
                title=title.get_text(strip=True),
                category="fashion",
                url=abs_url(base, link["href"] if link else "/sale"),
                discount=price.get_text(strip=True) if price else "Sale",
                expiry="While stocks last",
            )
        )
    return deals


def scrape_fashion() -> list[dict]:
    results: list[dict] = []
    for fn in (scrape_primark, scrape_hm, scrape_asos):
        try:
            results.extend(fn())
        except Exception as exc:
            logger.error("Fashion scraper %s failed: %s", fn.__name__, exc)
    return results
