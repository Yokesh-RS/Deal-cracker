"""Local relevance scoring (replaces Claude in deal-cracker 2)."""

from __future__ import annotations

from typing import Any

from app.tools.intent_parser import SearchIntent

SHOE_WORDS = ("shoe", "shoes", "trainer", "trainers", "sneaker", "footwear")


def _text(deal: dict[str, Any]) -> str:
    parts = [
        deal.get("store", ""),
        deal.get("title", ""),
        deal.get("offer", ""),
        deal.get("description", ""),
        deal.get("discount", ""),
        " ".join(deal.get("tags") or []),
    ]
    return " ".join(parts).lower()


def score_deal(deal: dict[str, Any], intent: SearchIntent) -> int:
    text = _text(deal)
    query = intent.raw_message.lower()
    score = 40

    if intent.store_terms:
        if any(t in text for t in intent.store_terms):
            score += 35
        else:
            score -= 25

    for word in query.split():
        if len(word) > 3 and word in text:
            score += 6

    if intent.student_only:
        if "student" in text or "student" in (deal.get("tags") or []):
            score += 25
        else:
            score -= 15

    if intent.product_filter == "shoes":
        if any(w in text for w in SHOE_WORDS):
            score += 20
        else:
            score -= 10

    if intent.store == "primark" and not intent.product_filter:
        if any(w in text for w in SHOE_WORDS) and "primark" not in text:
            score -= 30

    if deal.get("url"):
        score += 5

    if float(deal.get("price", 0)) > 0:
        score += 3

    return max(0, min(100, score))


def rank_by_relevance(deals: list[dict[str, Any]], intent: SearchIntent, limit: int = 3) -> list[dict[str, Any]]:
    for deal in deals:
        deal["score"] = score_deal(deal, intent)
        deal["matched_item"] = intent.raw_message[:60]

    min_score = 50 if intent.store else 35
    filtered = [d for d in deals if d.get("score", 0) >= min_score]

    if not filtered and deals:
        filtered = deals

    filtered.sort(
        key=lambda d: (-d.get("score", 0), float(d.get("price") or 9999), float(d.get("distance") or 999)),
    )
    return filtered[:limit]
