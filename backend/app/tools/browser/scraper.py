from __future__ import annotations

from typing import Any


def run(payload: dict[str, Any]) -> dict[str, Any]:
    url = payload.get("url")
    if not url:
        raise ValueError("url is required")
    return {
        "tool": "browser.scraper",
        "url": url,
        "content": f"Scraped content from {url}",
    }
