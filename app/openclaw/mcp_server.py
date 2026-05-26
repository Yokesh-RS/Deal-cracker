"""
Deal Cracker MCP server for OpenClaw.

Run:
    python -m app.openclaw.mcp_server

Add to your OpenClaw config (see openclaw/mcp-deal-cracker.example.json).
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise SystemExit(
        "MCP server requires Python 3.10+ and the `mcp` package.\n"
        "  pip install -r requirements-openclaw.txt\n"
        f"Original error: {exc}"
    ) from exc

from app.openclaw.mcp_tools import (
    mcp_parse_intent,
    mcp_search_by_store,
    mcp_search_deals,
    run_async,
)

mcp = FastMCP(
    "deal-cracker",
    instructions=(
        "Deal Cracker — search Glasgow-area deals from static data, "
        "retailer scrapers, and HotUKDeals. Always use tools before inventing offers."
    ),
)


@mcp.tool()
def search_deals(query: str, limit: int = 3) -> str:
    """
    Search deals for a natural-language query (coffee, primark, airport tickets, etc.).
    Returns JSON with headline and deals array including urls and prices.
    """
    return run_async(mcp_search_deals(query, limit=limit))


@mcp.tool()
def search_by_store(store_name: str, student_only: bool = False, limit: int = 3) -> str:
    """
    Find offers for one store only (starbucks, primark, blacksheep, etc.).
    Set student_only=true for student discounts.
    """
    return run_async(mcp_search_by_store(store_name, student_only=student_only, limit=limit))


@mcp.tool()
def parse_intent(query: str) -> str:
    """Parse a user message into categories, store name, and budget without searching."""
    return mcp_parse_intent(query)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
