"""OpenClaw bridge — connects Telegram agent to the gateway."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from app.openclaw.client import OpenClawClientError, OpenClawGatewayClient
from app.openclaw.config import OpenClawConfig, OpenClawMode, load_openclaw_config
from app.openclaw.prompt_builder import (
    build_agent_prompt,
    build_hybrid_prompt,
    build_system_context,
)

logger = logging.getLogger(__name__)


@dataclass
class OpenClawResult:
    """Result from OpenClaw orchestration."""

    intro_text: Optional[str]  # Optional message before deal cards
    used_openclaw: bool
    gateway_ok: bool
    mode: OpenClawMode


class OpenClawBridge:
    def __init__(self, config: Optional[OpenClawConfig] = None) -> None:
        self.config = config or load_openclaw_config()
        self._client = OpenClawGatewayClient(self.config)

    @property
    def mode(self) -> OpenClawMode:
        return self.config.mode

    def is_active(self) -> bool:
        return self.config.is_active

    async def health_check(self) -> bool:
        if not self.is_active():
            return False
        return await self._client.health_check()

    async def run_hybrid(
        self,
        user_message: str,
        deals: list[dict[str, Any]],
        headline: str,
        skills_md: str,
        system_prompt: str,
    ) -> OpenClawResult:
        """Local deals already fetched — OpenClaw adds a short intro."""
        if not self.is_active() or self.config.mode == OpenClawMode.OFF:
            return OpenClawResult(None, False, False, self.config.mode)

        if not deals:
            return OpenClawResult(None, False, False, self.config.mode)

        try:
            ctx = build_system_context(self.config, skills_md, system_prompt)
            hybrid = build_hybrid_prompt(user_message, deals, headline)
            intro = await self._client.execute(hybrid, system_context=ctx)
            return OpenClawResult(intro, True, True, self.config.mode)
        except OpenClawClientError as exc:
            logger.warning("OpenClaw hybrid failed: %s", exc)
            return OpenClawResult(None, False, False, self.config.mode)

    async def run_agent(
        self,
        user_message: str,
        skills_md: str,
        system_prompt: str,
    ) -> OpenClawResult:
        """Let OpenClaw agent handle the query (expects MCP tools configured)."""
        if not self.is_active() or self.config.mode != OpenClawMode.AGENT:
            return OpenClawResult(None, False, False, self.config.mode)

        try:
            ctx = build_system_context(self.config, skills_md, system_prompt)
            agent_prompt = build_agent_prompt(user_message, skills_md)
            reply = await self._client.execute(agent_prompt, system_context=ctx)
            return OpenClawResult(reply, True, True, self.config.mode)
        except OpenClawClientError as exc:
            logger.warning("OpenClaw agent mode failed: %s", exc)
            return OpenClawResult(None, False, False, self.config.mode)


_bridge: Optional[OpenClawBridge] = None


def get_openclaw_bridge() -> OpenClawBridge:
    global _bridge
    if _bridge is None:
        _bridge = OpenClawBridge()
    return _bridge
