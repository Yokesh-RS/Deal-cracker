# Deal Cracker 🦞🔥

**Deal Cracker** is a local AI-powered Telegram deals assistant for Glasgow, UK. Message the bot naturally — it understands what you want, searches a static deals database, ranks the best options (cheapest first, then nearest), and replies with concise nearby offers.

This is an **MVP prototype**: no live scraping yet. All deals come from `app/data/deals.json`.

## Features

- Natural-language queries (coffee, burgers, pizza, cinema, shoes, etc.)
- Intent/category detection with optional budget parsing (`under £50`)
- Static JSON deal database (Glasgow-area examples, GBP)
- Ranking engine: **cheapest → nearest → top 3**
- Telegram bot via `python-telegram-bot`
- FastAPI HTTP API for testing without Telegram
- **OpenClaw-compatible** layout: `skills.md`, system prompt, tool registry, optional gateway bridge

## Architecture

```
User (Telegram)
       │
       ▼
telegram_bot.py ──► agent.py (orchestration)
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   deal_search    nearby_search    ranking_engine
         │
         ▼
   data/deals.json
```

| Layer | Role |
|-------|------|
| **Telegram** | `telegram_bot.py` — polling, `/start`, `/help` |
| **Agent** | `agent.py` — intent, OpenClaw bridge stub, response formatting |
| **Tools** | `deal_search`, `nearby_search`, `ranking_engine` |
| **OpenClaw** | `skills.md` + `prompts/system_prompt.txt` + env-based gateway hook |
| **API** | `main.py` — FastAPI `/health`, `/chat` |

## Project structure

```
deal-cracker/
├── app/
│   ├── main.py              # FastAPI service
│   ├── agent.py             # Agent + OpenClaw bridge
│   ├── telegram_bot.py      # Bot entry point
│   ├── tools/
│   │   ├── deal_search.py
│   │   ├── nearby_search.py
│   │   └── ranking_engine.py
│   ├── data/
│   │   └── deals.json
│   └── prompts/
│       └── system_prompt.txt
├── skills.md
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone and enter the project

```bash
cd deal-cracker
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your Telegram token:

```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
```

### 4. Create a Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts.
3. Copy the token into `.env` as `TELEGRAM_BOT_TOKEN`.

## Running

### Telegram bot (primary)

From the `deal-cracker` directory:

```bash
python app/telegram_bot.py
```

The bot uses long polling. Send it a message in Telegram to test.

### FastAPI (optional)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Test the agent:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want coffee"}'
```

## Sample prompts

| You say | Typical category |
|---------|------------------|
| I want coffee | coffee |
| Cheap burgers nearby | burger |
| Any cinema deals? | cinema |
| Need shoes under £50 | fashion |
| Best pizza offers tonight | pizza |
| Cheap dinner nearby | food / burger |

Example reply:

```
🔥 Best coffee deals nearby:

1. McDonald's
   Regular Coffee
   £1.49
   600m away
   Any size coffee before 11am

2. Greggs
   Latte
   £2.10
   400m away
   Regular latte with loyalty card
...
```

## OpenClaw integration

Deal Cracker is structured for [OpenClaw](https://github.com/openclaw/openclaw) as the orchestration layer:

- **`skills.md`** — categories, tools, response style
- **`app/prompts/system_prompt.txt`** — agent behaviour
- **`OpenClawBridge`** in `agent.py` — set `OPENCLAW_ENABLED=true` when a gateway is available

MVP runs fully offline with local intent detection and tool calls. No OpenClaw install is required to try the bot.

## Future improvements

Planned extensions (architecture-ready, not implemented):

- Real retailer scraping pipelines
- Google Places API for live distance/location
- VoucherCodes and HotUKDeals integrations
- Vector search / embeddings for semantic matching
- User memory and personalization
- Location-aware recommendations from device GPS
- Full OpenClaw gateway tool-calling via `openclaw-sdk`

## License

MIT — use and extend freely for learning and prototypes.
