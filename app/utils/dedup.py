"""Deduplicate deals by store + title hash."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from app.scraper_config import SEEN_FILE

logger = logging.getLogger(__name__)


def deal_fingerprint(deal: dict[str, Any]) -> str:
    key = f"{deal.get('store', '')}|{deal.get('title', '')}|{deal.get('url', '')}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def dedupe_list(deals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for deal in deals:
        fp = deal_fingerprint(deal)
        if fp not in seen:
            seen.add(fp)
            out.append(deal)
    return out


def _load_seen() -> dict:
    if SEEN_FILE.exists():
        with open(SEEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def filter_seen(deals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = _load_seen()
    return [d for d in deals if deal_fingerprint(d) not in seen]
