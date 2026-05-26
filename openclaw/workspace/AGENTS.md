# Deal Cracker agent (OpenClaw)

Register this workspace in your OpenClaw gateway as agent id: **deal-cracker** (or set `OPENCLAW_AGENT_ID` to match).

## Required MCP server

Point OpenClaw at the Deal Cracker MCP server — see `openclaw/mcp-deal-cracker.example.json`.

Tools provided:

- `search_deals` — natural language search
- `search_by_store` — single-store offers
- `parse_intent` — intent only (debug)

## Telegram

The Python bot (`app/telegram_bot.py`) can run alongside OpenClaw:

- `OPENCLAW_MODE=hybrid` — local search + OpenClaw intro text
- `OPENCLAW_MODE=agent` — OpenClaw-first with local fallback
