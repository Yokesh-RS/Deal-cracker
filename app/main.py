"""
FastAPI service for Deal Cracker.

Health check and chat API for testing without Telegram.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

from app.agent import get_agent

app = FastAPI(
    title="Deal Cracker API",
    description="Local AI deals assistant — Glasgow MVP",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["I want coffee"])


class DealOut(BaseModel):
    store: str = ""
    title: str = ""
    price: float = 0
    url: str = ""
    score: int = 0


class ChatResponse(BaseModel):
    headline: str
    reply: str
    deals: list[DealOut] = []
    categories_detected: list[str] = []


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "deal-cracker"}


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    """Process a deal query (same logic as Telegram bot)."""
    from app.formatter import format_plain_list

    agent = get_agent()
    from app.agent import build_context

    ctx = build_context(body.message)
    response = await agent.process_message_async(body.message)
    reply = (
        format_plain_list(response.deals, response.headline)
        if response.deals
        else format_plain_list([], response.headline or "No deals")
    )
    deals_out = [
        DealOut(
            store=d.get("store", ""),
            title=d.get("title", ""),
            price=float(d.get("price", 0)),
            url=d.get("url", ""),
            score=int(d.get("score", 0)),
        )
        for d in response.deals
    ]
    return ChatResponse(
        headline=response.headline,
        reply=reply,
        deals=deals_out,
        categories_detected=ctx.categories,
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Deal Cracker",
        "docs": "/docs",
        "health": "/health",
    }
