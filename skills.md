# Deal Cracker — OpenClaw Skills

## Agent identity

**Name:** Deal Cracker  
**Role:** Local AI-powered deals assistant (Glasgow, UK MVP)  
**Channel:** Telegram  

## Supported categories

| Category   | Example user phrases                          |
|-----------|------------------------------------------------|
| coffee    | "I want coffee", "Need a latte nearby"         |
| burger    | "Cheap burgers", "burger deals"                |
| food      | "Cheap dinner nearby", "lunch deals"           |
| pizza     | "Best pizza offers tonight", "pizza deals"     |
| cinema    | "Any cinema deals?", "movie tickets"             |
| shopping  | "Shopping deals", general retail               |
| fashion   | "Need shoes under £50", trainers, clothes      |
| travel    | "Ticket to airport", flights, Glasgow Airport  |

## Capabilities (MVP)

- Natural-language intent detection (category + optional max price)
- Static JSON deal search + live scrape (HotUKDeals, MyVoucherCodes)
- Offer links (🔗) on every result where available
- Store-specific search (Primark ≠ all shoe shops)
- Student-offer filtering
- Nearby-first filtering via distance metadata
- Ranking: cheapest → nearest → top 3
- Concise Telegram-formatted replies

## Available tools

| Tool              | Module                    | Description                          |
|-------------------|---------------------------|--------------------------------------|
| `deal_search`     | `app.tools.deal_search`   | Filter deals by category / price cap |
| `nearby_search`   | `app.tools.nearby_search` | Filter by max distance (km)          |
| `ranking_engine`  | `app.tools.ranking_engine`| Sort and return top N deals          |

## Response style

- Lead with a category emoji headline, e.g. "🔥 Best coffee deals nearby:"
- Numbered list (max 3 items)
- Each item: store, title, price, distance, offer (one line each)
- No long paragraphs; mobile-friendly

## OpenClaw integration

This project is structured for OpenClaw gateway tool-calling:

- `skills.md` — skill registry (this file)
- `app/prompts/system_prompt.txt` — agent system prompt
- `app/agent.py` — orchestration layer with pluggable `OpenClawBridge`

Set `OPENCLAW_ENABLED=true` and `OPENCLAW_GATEWAY_URL` when a live gateway is available.  
MVP runs local intent + tools without requiring the gateway.

## Future skills (planned)

- `scrape_retailers` — live deal scraping
- `google_places` — real location + distance
- `vouchercodes` — voucher API integration
- `hotukdeals` — community deal feed
- `vector_search` — semantic deal matching
- `user_memory` — personalization and preferences
