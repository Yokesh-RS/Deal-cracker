"""Filter deals by proximity (static distance field in km)."""

from typing import Any, Optional


def filter_by_max_distance(
    deals: list[dict[str, Any]],
    max_km: Optional[float] = None,
) -> list[dict[str, Any]]:
    """
    Keep only deals within `max_km` kilometres.
    If max_km is None, return all deals unchanged.
    """
    if max_km is None:
        return deals
    return [d for d in deals if float(d.get("distance", 999)) <= max_km]


def format_distance(distance_km: float) -> str:
    """Human-readable distance for Telegram replies."""
    if distance_km < 1:
        metres = int(round(distance_km * 1000))
        return f"{metres}m away"
    return f"{distance_km:.1f}km away"
