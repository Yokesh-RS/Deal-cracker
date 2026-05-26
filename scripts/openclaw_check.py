#!/usr/bin/env python3
"""Check OpenClaw gateway connectivity for Deal Cracker."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


async def main() -> None:
    from app.openclaw import get_openclaw_bridge, load_openclaw_config

    cfg = load_openclaw_config()
    print(f"OPENCLAW_ENABLED: {cfg.enabled}")
    print(f"OPENCLAW_MODE:    {cfg.mode.value}")
    print(f"Agent ID:         {cfg.agent_id}")
    print(f"HTTP gateway:     {cfg.gateway_http_url}")
    print(f"WS gateway:       {cfg.gateway_ws_url}")

    if not cfg.is_active:
        print("\nOpenClaw is OFF. Set OPENCLAW_ENABLED=true in .env")
        return

    bridge = get_openclaw_bridge()
    ok = await bridge.health_check()
    print(f"\nGateway reachable: {'yes' if ok else 'no'}")

    if ok:
        try:
            from app.agent import load_skills, load_system_prompt

            reply = await bridge._client.execute(
                "Say 'Deal Cracker is connected' in one short sentence.",
                system_context=load_system_prompt(),
            )
            print(f"Test reply: {reply[:200]}")
        except Exception as exc:
            print(f"Execute test failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
