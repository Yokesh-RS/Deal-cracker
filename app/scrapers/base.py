"""Shared scraper utilities."""

from __future__ import annotations

import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.scraper_config import SCRAPER_HEADERS, SCRAPER_TIMEOUT

logger = logging.getLogger(__name__)


def get_soup(url: str, timeout: Optional[int] = None) -> Optional[BeautifulSoup]:
    try:
        response = requests.get(
            url,
            headers=SCRAPER_HEADERS,
            timeout=timeout or SCRAPER_TIMEOUT,
        )
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as exc:
        logger.error("GET %s failed: %s", url, exc)
        return None


def abs_url(base: str, href: Optional[str]) -> str:
    if not href:
        return base
    if href.startswith("http"):
        return href
    return urljoin(base, href)


def parse_price_from_text(text: str) -> float:
    if not text:
        return 0.0
    match = re.search(r"£\s*(\d+(?:\.\d+)?)", text.replace(",", ""))
    if match:
        return float(match.group(1))
    return 0.0


def make_deal(
    store: str,
    title: str,
    category: str,
    url: str,
    description: str = "",
    discount: str = "",
    expiry: str = "See website",
    coupon: Optional[str] = None,
    source: str = "scraper",
) -> dict[str, Any]:
    price = parse_price_from_text(discount) or parse_price_from_text(description)
    return {
        "store": store,
        "title": title,
        "description": description,
        "discount": discount,
        "offer": description or discount,
        "price": price,
        "distance": 0.0,
        "url": url,
        "category": category,
        "expiry": expiry,
        "coupon": coupon,
        "source": source,
        "tags": [],
    }
