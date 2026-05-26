"""Build prompts sent to OpenClaw with deal context."""

from __future__ import annotations

import json
from typing import Any

from app.openclaw.config import OpenClawConfig


def build_system_context(config: OpenClawConfig, skills_md: str, system_prompt: str) -> str:
    return f"""You are Deal Cracker, a Glasgow UK deals assistant integrated with OpenClaw.

Project root: {config.project_root}

## Instructions
{system_prompt.strip()}

## Skills registry
{skills_md.strip()}

## Rules for this session
- Use the deal data provided below when answering; do not invent stores or prices.
- Keep replies concise and mobile-friendly.
- Include offer URLs when present.
- If deal data is empty, say so and suggest another query.
"""


def build_hybrid_prompt(
    user_message: str,
    deals: list[dict[str, Any]],
    headline: str,
) -> str:
    """Ask OpenClaw to polish the reply using pre-fetched deals."""
    deals_json = json.dumps(deals, indent=2, default=str)[:12000]
    return f"""The user asked: "{user_message}"

Headline already chosen: {headline}

Deals found (JSON — do not change prices or invent new ones):
{deals_json}

Write a short friendly intro (1-2 sentences) for Telegram, then confirm the top deals match their request.
Do not repeat the full deal list — the bot sends formatted cards separately.
"""


def build_agent_prompt(user_message: str, skills_md: str) -> str:
    """Agent mode: OpenClaw should use MCP tools to search deals."""
    return f"""User request: {user_message}

Use the Deal Cracker MCP tools (search_deals, search_by_store) to find real offers before answering.
Return a brief summary; the Telegram bot will show detailed cards from tool results when available.

Skills reference:
{skills_md[:2000]}
"""
