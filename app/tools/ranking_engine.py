"""Rank deals by price (cheapest first) then distance (nearest first)."""

from typing import Any


def rank_deals(deals: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    """
    Sort deals: lowest price first, then shortest distance.
    Returns at most `limit` results (default top 3).
    """
    if not deals:
        return []

    sorted_deals = sorted(
        deals,
        key=lambda d: (float(d.get("price", 9999)), float(d.get("distance", 9999))),
    )
    return sorted_deals[:limit]
