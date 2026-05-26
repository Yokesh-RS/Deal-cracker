"""Deal Cracker tools exposed to OpenClaw via MCP."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.tools.deal_search import search_all_async
from app.tools.intent_parser import parse_intent
from app.tools.local_scoring import rank_by_relevance
from app.scraper_config import TOP_DEALS_COUNT


async def mcp_search_deals(query: str, limit: int = 3) -> str:
    """
    Search static data, live scrapers, and HotUKDeals for a natural-language query.
    Returns JSON list of top deals.
    """
    intent = parse_intent(query)
    raw = await search_all_async(intent)
    ranked = rank_by_relevance(raw, intent, limit=min(limit, TOP_DEALS_COUNT))
    return json.dumps(
        {
            "headline": intent.headline,
            "categories": intent.categories,
            "store": intent.store,
            "deals": ranked,
        },
        indent=2,
        default=str,
    )


async def mcp_search_by_store(store_name: str, student_only: bool = False, limit: int = 3) -> str:
    """Search deals for a specific store (e.g. primark, starbucks, blacksheep)."""
    flags = " student" if student_only else ""
    return await mcp_search_deals(f"offers at {store_name}{flags}", limit=limit)


def mcp_parse_intent(query: str) -> str:
    """Parse user message into categories, store, and budget without searching."""
    intent = parse_intent(query)
    return json.dumps(
        {
            "categories": intent.categories,
            "store": intent.store,
            "store_terms": intent.store_terms,
            "student_only": intent.student_only,
            "max_price": intent.max_price,
            "scrape_query": intent.scrape_query,
            "headline": intent.headline,
        },
        indent=2,
    )


def run_async(coro):
    """Run async tool from sync MCP handler."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as pool:
        return pool.submit(asyncio.run, coro).result()
