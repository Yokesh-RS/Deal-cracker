"""Connect to OpenClaw gateway via SDK (3.11+) or HTTP fallback."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

from app.openclaw.config import OpenClawConfig

logger = logging.getLogger(__name__)


class OpenClawClientError(Exception):
    pass


class OpenClawGatewayClient:
    """Thin client: prefers openclaw-sdk, falls back to HTTP execute endpoint."""

    def __init__(self, config: OpenClawConfig) -> None:
        self.config = config
        self._sdk_client: Any = None

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                headers = self._auth_headers()
                for path in ("/agents/health", "/health", "/"):
                    url = f"{self.config.gateway_http_url}{path}"
                    resp = await client.get(url, headers=headers)
                    if resp.status_code < 500:
                        return True
        except Exception as exc:
            logger.debug("Gateway health check failed: %s", exc)
        return await self._sdk_ping()

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def _sdk_ping(self) -> bool:
        try:
            from openclaw_sdk import OpenClawClient  # type: ignore
        except ImportError:
            return False
        try:
            async with OpenClawClient.connect(
                gateway_ws_url=self.config.gateway_ws_url,
                api_key=self.config.api_key or None,
                timeout=self.config.timeout_seconds,
            ) as client:
                agent = client.get_agent(self.config.agent_id)
                _ = agent.session_key
                return True
        except Exception as exc:
            logger.debug("SDK ping failed: %s", exc)
            return False

    async def execute(self, user_message: str, system_context: str = "") -> str:
        """
        Run the configured OpenClaw agent with optional extra system context.
        Returns assistant text content.
        """
        prompt = user_message
        if system_context:
            prompt = f"{system_context.strip()}\n\n---\n\nUser message: {user_message}"

        content = await self._execute_sdk(prompt)
        if content:
            return content

        content = await self._execute_http(prompt)
        if content:
            return content

        raise OpenClawClientError(
            "Could not reach OpenClaw gateway. "
            "Start it with `openclaw gateway status` and check OPENCLAW_GATEWAY_URL."
        )

    async def _execute_sdk(self, prompt: str) -> Optional[str]:
        try:
            from openclaw_sdk import OpenClawClient  # type: ignore
        except ImportError:
            logger.info("openclaw-sdk not installed — using HTTP fallback (pip install openclaw-sdk)")
            return None

        try:
            async with OpenClawClient.connect(
                gateway_ws_url=self.config.gateway_ws_url,
                api_key=self.config.api_key or None,
                timeout=self.config.timeout_seconds,
            ) as client:
                agent = client.get_agent(
                    self.config.agent_id,
                    session_name=self.config.session_name,
                )
                result = await agent.execute(prompt)
                if getattr(result, "success", True) and getattr(result, "content", None):
                    return str(result.content).strip()
                if getattr(result, "content", None):
                    return str(result.content).strip()
        except Exception as exc:
            logger.warning("OpenClaw SDK execute failed: %s", exc)
        return None

    async def _execute_http(self, prompt: str) -> Optional[str]:
        """POST to community / FastAPI-style execute routes."""
        paths = [
            f"/agents/{self.config.agent_id}/execute",
            f"/v1/agents/{self.config.agent_id}/execute",
            "/execute",
        ]
        bodies = [
            {"query": prompt, "message": prompt, "input": prompt},
            {"messages": [{"role": "user", "content": prompt}]},
        ]

        async with httpx.AsyncClient(timeout=float(self.config.timeout_seconds)) as client:
            for path in paths:
                url = f"{self.config.gateway_http_url}{path}"
                for body in bodies:
                    try:
                        resp = await client.post(url, json=body, headers=self._auth_headers())
                        if resp.status_code == 404:
                            continue
                        resp.raise_for_status()
                        text = _extract_text_from_response(resp.json())
                        if text:
                            return text
                    except httpx.HTTPStatusError as exc:
                        logger.debug("HTTP %s %s: %s", path, exc.response.status_code, exc)
                    except Exception as exc:
                        logger.debug("HTTP execute %s failed: %s", path, exc)
        return None


def _extract_text_from_response(data: Any) -> str:
    if isinstance(data, str):
        return data.strip()
    if not isinstance(data, dict):
        return ""

    for key in ("content", "reply", "result", "output", "text", "message"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        msg = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        if isinstance(msg, dict) and msg.get("content"):
            return str(msg["content"]).strip()

    return json.dumps(data, indent=2)[:4000]
