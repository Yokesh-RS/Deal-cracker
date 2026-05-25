"""
FastAPI service for Deal Cracker.

Health check and chat API for testing without Telegram.
Future: OpenClaw-compatible REST routes and webhooks.
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


class ChatResponse(BaseModel):
    reply: str
    categories_detected: list[str] = []


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "deal-cracker"}


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    """Process a deal query (same logic as Telegram bot)."""
    agent = get_agent()
    from app.agent import build_context

    ctx = build_context(body.message)
    reply = await agent.process_message_async(body.message)
    return ChatResponse(reply=reply, categories_detected=ctx.categories)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Deal Cracker",
        "docs": "/docs",
        "health": "/health",
    }
