"""Category scraper registry."""

from app.scrapers.delivery import scrape_delivery
from app.scrapers.ecommerce import scrape_ecommerce
from app.scrapers.entertainment import scrape_entertainment
from app.scrapers.fashion import scrape_fashion
from app.scrapers.food import scrape_food
from app.scrapers.grocery import scrape_grocery
from app.scrapers.travel import scrape_travel

from typing import Callable

SCRAPER_REGISTRY: dict[str, Callable[[], list]] = {
    "food": scrape_food,
    "fashion": scrape_fashion,
    "ecommerce": scrape_ecommerce,
    "grocery": scrape_grocery,
    "travel": scrape_travel,
    "entertainment": scrape_entertainment,
    "delivery": scrape_delivery,
}

__all__ = ["SCRAPER_REGISTRY", "scrape_food", "scrape_fashion", "scrape_travel"]
