# Deal Cracker 🚀

Deal Cracker is an AI-powered Telegram deals assistant for Glasgow, UK.

Users can message the bot naturally (for example: “cheap coffee nearby” or “student cinema deals”), and the assistant returns the best nearby offers ranked by:

* Cheapest first
* Nearest first
* Most relevant category

The project is built using:

* Python
* Telegram Bot API
* FastAPI
* OpenClaw-compatible agent architecture
* Static deal database (MVP)

---

# Demo Use Cases

Users can ask:

* “cheap coffee nearby”
* “best burger deals tonight”
* “student cinema offers”
* “Primark discounts”
* “pizza under £10”
* “travel deals to Edinburgh”

Example response:

🔥 Best coffee deals nearby

1. Starbucks
   £2.50
   Glasgow Central
   https://starbucks.co.uk

2. Greggs
   £1.90
   Buchanan Street
   https://greggs.co.uk

---

# Features

✅ Natural language deal search
✅ Telegram bot interface
✅ FastAPI backend
✅ Deal ranking engine
✅ OpenClaw-compatible architecture
✅ Static JSON deal database
✅ Budget-aware search (`under £20`)
✅ Category detection
✅ Mobile-friendly responses

---

# Tech Stack

| Layer          | Technology            |
| -------------- | --------------------- |
| Bot            | Telegram Bot API      |
| Backend        | FastAPI               |
| Agent          | Python local agent    |
| AI Integration | OpenClaw-compatible   |
| Database       | Static JSON           |
| Ranking        | Custom scoring engine |
| Environment    | Python virtualenv     |

---

# Project Structure

```bash
deal-cracker/
│
├── app/
│   ├── telegram_bot.py
│   ├── main.py
│   ├── agent.py
│   ├── formatter.py
│   │
│   ├── tools/
│   │   ├── deal_search.py
│   │   ├── nearby_search.py
│   │   └── ranking_engine.py
│   │
│   ├── data/
│   │   └── deals.json
│   │
│   └── prompts/
│       └── system_prompt.txt
│
├── skills.md
├── requirements.txt
├── .env.example
└── README.md
```

---

# How It Works

```text
Telegram User
      ↓
telegram_bot.py
      ↓
agent.py
      ↓
Intent Parser + Ranking Engine
      ↓
deals.json
      ↓
Top 3 ranked deals returned
```

---

# Setup Instructions

## 1. Clone Repository

```bash
git clone https://github.com/Yokesh-RS/Deal-cracker
cd deal-cracker
```

---

## 2. Create Virtual Environment

```bash
python3 -m venv .venv
```

Activate environment:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create `.env`

```bash
cp .env.example .env
```

Add Telegram Bot Token:

```env
TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
```

---

# Create Telegram Bot

1. Open Telegram
2. Search for `@BotFather`
3. Run:

```text
/newbot
```

4. Copy generated token
5. Paste into `.env`

---

# Running the Project

## Main Execution (Telegram Bot)

Start the Telegram bot:

```bash
python app/telegram_bot.py
```

This is the primary entry point of the application.

Once running:

1. Open Telegram
2. Search for your bot
3. Start chatting

Example:

```text
cheap coffee nearby
```

---

# Optional: Run FastAPI Server

```bash
uvicorn app.main:app --reload --port 8000
```

Test endpoint:

```bash
curl -X POST http://localhost:8000/chat \
-H "Content-Type: application/json" \
-d '{"message":"cheap pizza"}'
```

---

# OpenClaw Integration

This project is designed to be OpenClaw-compatible.

The repository includes:

* `skills.md`
* agent architecture
* MCP-ready structure
* OpenClaw gateway hooks

Future versions can connect directly to:

* OpenClaw agents
* Ollama
* MCP tools
* live scraping systems

---

# Current MVP Scope

This version currently uses:

```text
app/data/deals.json
```

as the deal source.

No live web scraping is enabled yet.

The architecture is intentionally designed so live APIs and scrapers can be added later without changing the Telegram workflow.

---

# Future Improvements

* Live retailer scraping
* Google Maps integration
* User location awareness
* Vector search / embeddings
* Personalized deal recommendations
* Travel APIs
* Student discount integrations
* Real-time notifications

---

# Example Queries

| Query                     | Intent  |
| ------------------------- | ------- |
| cheap coffee nearby       | coffee  |
| pizza under £10           | food    |
| cinema deals tonight      | cinema  |
| Primark offers            | fashion |
| cheap travel to Edinburgh | travel  |


```
```
