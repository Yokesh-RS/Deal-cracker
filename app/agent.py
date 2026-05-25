"""
Deal Cracker agent layer — OpenClaw-compatible orchestration.

Uses intent parsing, static JSON, and live scraping (HotUKDeals / vouchers).
"""

from __future__ import annotations

import os
from typing import Any, Optional

from app.tools.deal_search import search_all
from app.tools.intent_parser import SearchIntent, parse_intent
from app.tools.nearby_search import filter_by_max_distance, format_distance
from app.tools.ranking_engine import rank_deals

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
SKILLS_PATH = Path(__file__).resolve().parent.parent / "skills.md"


def load_system_prompt() -> str:
    path = PROMPTS_DIR / "system_prompt.txt"
    return path.read_text(encoding="utf-8")


def load_skills() -> str:
    if SKILLS_PATH.exists():
        return SKILLS_PATH.read_text(encoding="utf-8")
    return ""


def format_price(price: float) -> str:
    if price <= 0:
        return "See offer"
    if price == int(price):
        return f"£{int(price)}"
    return f"£{price:.2f}"


def format_deal_list(
    deals: list[dict[str, Any]],
    headline: str,
    *,
    live_count: int = 0,
) -> str:
    if not deals:
        hints = (
            "😕 No matching deals right now.\n\n"
            "Try:\n"
            "• Blacksheep coffee offers\n"
            "• Student offers at Starbucks\n"
            "• Primark clothing deals\n"
            "• Cheap flights / Glasgow airport"
        )
        if live_count == 0 and os.getenv("SCRAPING_ENABLED", "true").lower() != "false":
            hints += "\n\n(Live scrape returned nothing — check connection or try another phrase.)"
        return hints

    lines = [headline, ""]
    for i, deal in enumerate(deals, start=1):
        store = deal.get("store", "Unknown")
        title = deal.get("title", "Deal")
        price = format_price(float(deal.get("price", 0)))
        distance = deal.get("distance", 0)
        dist_str = (
            format_distance(float(distance))
            if float(distance) > 0
            else "Online / UK-wide"
        )
        offer = deal.get("offer", "")
        url = deal.get("url", "")
        source = deal.get("source", "local")

        lines.append(f"{i}. {store}")
        lines.append(f"   {title}")
        lines.append(f"   {price}")
        lines.append(f"   {dist_str}")
        lines.append(f"   {offer}")
        if url:
            lines.append(f"   🔗 {url}")
        elif source == "local":
            lines.append(f"   🔗 (in-store — ask at {store})")
        if i < len(deals):
            lines.append("")

    if live_count:
        lines.append("")
        lines.append(f"📡 Includes {live_count} live deal(s) from the web.")
    return "\n".join(lines)


def run_tool_pipeline(intent: SearchIntent) -> tuple[list[dict[str, Any]], int]:
    raw = search_all(intent)
    live_n = sum(1 for d in raw if d.get("source") in ("hotukdeals", "myvouchercodes"))
    filtered = filter_by_max_distance(raw, None)
    ranked = rank_deals(filtered, limit=3)
    return ranked, live_n


class OpenClawBridge:
    def __init__(self) -> None:
        self.enabled = os.getenv("OPENCLAW_ENABLED", "false").lower() == "true"
        self.gateway_url = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
        self.agent_id = os.getenv("OPENCLAW_AGENT_ID", "deal-cracker")

    def is_available(self) -> bool:
        return self.enabled

    async def execute(self, message: str) -> Optional[str]:
        if not self.enabled:
            return None
        return None


class DealCrackerAgent:
    def __init__(self) -> None:
        self.system_prompt = load_system_prompt()
        self.skills = load_skills()
        self.openclaw = OpenClawBridge()

    def process_message(self, message: str) -> str:
        message = (message or "").strip()
        if not message:
            return (
                "👋 Hi! I'm Deal Cracker.\n\n"
                "Ask me things like:\n"
                "• I want coffee\n"
                "• Student offers at Starbucks\n"
                "• Any offers on Primark\n"
                "• Cheap ticket to the airport\n"
                "• Need shoes under £50"
            )

        intent = parse_intent(message)
        deals, live_n = run_tool_pipeline(intent)
        return format_deal_list(deals, intent.headline, live_count=live_n)

    async def process_message_async(self, message: str) -> str:
        if self.openclaw.is_available():
            gateway_reply = await self.openclaw.execute(message)
            if gateway_reply:
                return gateway_reply
        return self.process_message(message)


_agent: Optional[DealCrackerAgent] = None


def get_agent() -> DealCrackerAgent:
    global _agent
    if _agent is None:
        _agent = DealCrackerAgent()
    return _agent


# Backwards compatibility for FastAPI
def build_context(message: str) -> SearchIntent:
    return parse_intent(message)
