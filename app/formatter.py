"""
Telegram message formatting (deal-cracker 2 style).
Uses Markdown: bold titles, clickable Shop now links.
"""

from __future__ import annotations

import re
from typing import Any


def _escape_md(text: str) -> str:
    """Escape Telegram Markdown special chars in user content."""
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!])", r"\\\1", text or "")


def format_price_line(deal: dict[str, Any]) -> str:
    price = float(deal.get("price", 0))
    discount = deal.get("discount") or deal.get("offer", "")
    if price > 0:
        p = f"£{int(price)}" if price == int(price) else f"£{price:.2f}"
        return f"💰 {p}" + (f" — {discount}" if discount and discount != p else "")
    if discount:
        return f"💰 Save: {discount}"
    return ""


def format_deal_card(deal: dict[str, Any]) -> str:
    store = _escape_md(deal.get("store", "Unknown"))
    title = _escape_md(deal.get("title", "Deal"))
    description = deal.get("description") or deal.get("offer", "")
    if description and description.lower() != deal.get("title", "").lower():
        description = _escape_md(description)
    else:
        description = ""

    expiry = deal.get("expiry", "See website")
    coupon = deal.get("coupon")
    url = deal.get("url", "")
    matched = deal.get("matched_item", "")
    score = int(deal.get("score", 0))

    filled = round(score / 20) if score else 0
    score_bar = "⭐" * filled + "☆" * (5 - filled)

    expiry_line = f"Valid until: {_escape_md(str(expiry))}"
    if expiry and "hour" in str(expiry).lower():
        expiry_line = f"⏰ *Expires soon:* {_escape_md(str(expiry))}"

    coupon_line = f"🎟 Coupon: `{coupon}`" if coupon else ""

    distance = float(deal.get("distance", 0))
    if distance > 0:
        metres = int(round(distance * 1000)) if distance < 1 else None
        loc = f"{metres}m away" if metres else f"{distance:.1f}km away"
        location_line = f"📍 {loc}"
    else:
        location_line = "📍 Online / UK-wide"

    price_line = format_price_line(deal)
    match_line = f'✅ Matches: *"{_escape_md(matched)}"*' if matched else ""

    lines = [
        f"🏷 *{store}* — {title}",
        description,
        price_line,
        location_line,
        expiry_line,
        coupon_line,
        match_line,
        score_bar if score else "",
        f"[Shop now →]({url})" if url else "",
    ]
    return "\n".join(line for line in lines if line).strip()


def format_results_header(headline: str, count: int) -> str:
    return f"{headline}\n\nFound *{count}* deal(s) 👇\n━━━━━━━━━━━━━━━"


def format_no_deals(query: str = "") -> str:
    base = "😕 No matching deals right now."
    if query:
        base += f"\n\nNothing strong for *{_escape_md(query)}* — try another shop or category."
    base += (
        "\n\nTry:\n"
        "• `blacksheep coffee`\n"
        "• `student offers at Starbucks`\n"
        "• `Primark offers`\n"
        "• `ticket to airport`"
    )
    return base


def format_plain_list(deals: list[dict[str, Any]], headline: str) -> str:
    """Fallback plain-text list (no Markdown)."""
    if not deals:
        return format_no_deals()
    lines = [headline, ""]
    for i, deal in enumerate(deals, 1):
        lines.append(f"{i}. {deal.get('store')} — {deal.get('title')}")
        if deal.get("url"):
            lines.append(f"   {deal['url']}")
    return "\n".join(lines)
