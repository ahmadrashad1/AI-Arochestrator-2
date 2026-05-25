from __future__ import annotations

from typing import Any


def run(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload.get("query") or payload.get("company") or payload.get("goal")
    if not query:
        raise ValueError("query is required")
    return {
        "tool": "browser.search",
        "query": query,
        "results": [
            {"title": f"{query} overview", "url": f"https://example.com/{str(query).replace(' ', '-').lower()}"},
            {"title": f"{query} pricing", "url": f"https://example.com/{str(query).replace(' ', '-').lower()}/pricing"},
        ],
    }
