from __future__ import annotations

import pytest

from app.tools.registry import run_tool


def test_async_tool_runs_inline():
    res = run_tool("async_echo", {"x": 1}, timeout_seconds=2, sandbox=False)
    assert isinstance(res, dict)
    assert res.get("tool") == "async_echo"


def test_async_tool_sandbox_timeout():
    # run the async tool in a sandbox with a small timeout to ensure sandbox path works
    res = run_tool("async_echo", {"y": 2}, timeout_seconds=2, sandbox=True)
    assert isinstance(res, dict)
    assert res.get("received") == {"y": 2}
