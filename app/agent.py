"""
Deal Cracker agent — local pipeline + OpenClaw orchestration.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.formatter import format_no_deals, format_plain_list
from app.openclaw import get_openclaw_bridge
from app.openclaw.config import OpenClawMode
from app.scraper_config import TOP_DEALS_COUNT
from app.tools.deal_search import search_all_async
from app.tools.intent_parser import SearchIntent, parse_intent
from app.tools.local_scoring import rank_by_relevance

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
SKILLS_PATH = Path(__file__).resolve().parent.parent / "skills.md"


@dataclass
class AgentResponse:
    headline: str
    deals: list[dict[str, Any]]
    query: str = ""
    openclaw_intro: Optional[str] = None
    openclaw_used: bool = False


def load_system_prompt() -> str:
    return (PROMPTS_DIR / "system_prompt.txt").read_text(encoding="utf-8")


def load_skills() -> str:
    if SKILLS_PATH.exists():
        return SKILLS_PATH.read_text(encoding="utf-8")
    return ""


class DealCrackerAgent:
    def __init__(self) -> None:
        self.system_prompt = load_system_prompt()
        self.skills = load_skills()
        self.openclaw = get_openclaw_bridge()

    async def process_message_async(self, message: str) -> AgentResponse:
        message = (message or "").strip()
        if not message:
            return AgentResponse(headline="👋 Deal Cracker", deals=[], query="")

        intent = parse_intent(message)
        raw = await search_all_async(intent)
        deals = rank_by_relevance(raw, intent, limit=TOP_DEALS_COUNT)

        intro: Optional[str] = None
        openclaw_used = False

        if self.openclaw.is_active():
            if self.openclaw.mode == OpenClawMode.AGENT:
                oc = await self.openclaw.run_agent(
                    message, self.skills, self.system_prompt
                )
                if oc.gateway_ok and oc.intro_text:
                    intro = oc.intro_text
                    openclaw_used = True
            elif self.openclaw.mode == OpenClawMode.HYBRID and deals:
                oc = await self.openclaw.run_hybrid(
                    message,
                    deals,
                    intent.headline,
                    self.skills,
                    self.system_prompt,
                )
                if oc.gateway_ok and oc.intro_text:
                    intro = oc.intro_text
                    openclaw_used = True

        return AgentResponse(
            headline=intent.headline,
            deals=deals,
            query=message,
            openclaw_intro=intro,
            openclaw_used=openclaw_used,
        )

    def process_message(self, message: str) -> str:
        response = asyncio.run(self.process_message_async(message))
        if not (message or "").strip():
            return (
                "👋 Hi! I'm Deal Cracker.\n\n"
                "Try: blacksheep coffee, student offers at Starbucks, Primark offers"
            )
        if not response.deals and not response.openclaw_intro:
            return format_no_deals(response.query)
        parts = []
        if response.openclaw_intro:
            parts.append(response.openclaw_intro)
        if response.deals:
            parts.append(format_plain_list(response.deals, response.headline))
        elif not response.openclaw_intro:
            parts.append(format_no_deals(response.query))
        return "\n\n".join(parts)


_agent: Optional[DealCrackerAgent] = None


def get_agent() -> DealCrackerAgent:
    global _agent
    if _agent is None:
        _agent = DealCrackerAgent()
    return _agent


def build_context(message: str) -> SearchIntent:
    return parse_intent(message)
