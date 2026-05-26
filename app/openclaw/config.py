"""OpenClaw connection settings from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class OpenClawMode(str, Enum):
    """How Deal Cracker uses OpenClaw."""

    OFF = "off"  # Local pipeline only
    HYBRID = "hybrid"  # Local deals + OpenClaw formats / reasons (default when enabled)
    AGENT = "agent"  # OpenClaw agent first; local fallback on failure


@dataclass
class OpenClawConfig:
    enabled: bool
    mode: OpenClawMode
    agent_id: str
    session_name: str
    gateway_ws_url: str
    gateway_http_url: str
    api_key: str
    timeout_seconds: int
    fallback_to_local: bool
    project_root: str

    @property
    def is_active(self) -> bool:
        return self.enabled and self.mode != OpenClawMode.OFF


def load_openclaw_config() -> OpenClawConfig:
    enabled = os.getenv("OPENCLAW_ENABLED", "false").lower() in ("true", "1", "yes")
    mode_str = os.getenv("OPENCLAW_MODE", "hybrid").lower()
    try:
        mode = OpenClawMode(mode_str)
    except ValueError:
        mode = OpenClawMode.HYBRID if enabled else OpenClawMode.OFF

    if not enabled:
        mode = OpenClawMode.OFF

    ws = os.getenv("OPENCLAW_GATEWAY_WS_URL", "ws://127.0.0.1:18789/gateway")
    http = os.getenv(
        "OPENCLAW_GATEWAY_URL",
        os.getenv("OPENCLAW_OPENAI_BASE_URL", "http://127.0.0.1:18789"),
    ).rstrip("/")

    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent

    return OpenClawConfig(
        enabled=enabled,
        mode=mode,
        agent_id=os.getenv("OPENCLAW_AGENT_ID", "deal-cracker"),
        session_name=os.getenv("OPENCLAW_SESSION_NAME", "telegram"),
        gateway_ws_url=ws,
        gateway_http_url=http,
        api_key=os.getenv("OPENCLAW_API_KEY", os.getenv("OPENCLAW_GATEWAY_TOKEN", "")),
        timeout_seconds=int(os.getenv("OPENCLAW_TIMEOUT", "120")),
        fallback_to_local=os.getenv("OPENCLAW_FALLBACK_LOCAL", "true").lower() != "false",
        project_root=str(root),
    )
