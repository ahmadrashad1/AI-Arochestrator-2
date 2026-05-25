from __future__ import annotations

import pytest

from app.tools.registry import run_tool


def test_nested_tool_resolution_and_validation() -> None:
    search_result = run_tool("browser.search", {"query": "acme sales"})
    assert search_result["tool"] == "browser.search"
    assert search_result["results"]

    with pytest.raises(PermissionError):
        run_tool("communication.gmail", {"to": "lead@example.com", "subject": "Hi", "body": "Hello", "allow_send": False})

    with pytest.raises(TimeoutError):
        run_tool("browser.playwright", {"action": "sleep", "seconds": 2}, sandbox="process", timeout_seconds=1)

    with pytest.raises(ValueError):
        run_tool("browser.search", {})
