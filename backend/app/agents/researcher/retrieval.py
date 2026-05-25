from __future__ import annotations

from typing import Any

from app.tools.browser.search_tool import run as browser_search
from app.tools.browser.scraper import run as scrape_page


def gather_lead_context(input_payload: dict[str, Any]) -> dict[str, Any]:
    query = input_payload.get("research_query") or input_payload.get("goal") or input_payload.get("company") or "lead generation"
    search_results = browser_search({"query": query, "company": input_payload.get("company")})
    scraped = scrape_page({"url": input_payload.get("website") or input_payload.get("url") or "https://example.com"})
    return {
        "query": query,
        "company": input_payload.get("company"),
        "search_results": search_results,
        "scraped_page": scraped,
        "summary": f"Collected context for {query}",
    }
