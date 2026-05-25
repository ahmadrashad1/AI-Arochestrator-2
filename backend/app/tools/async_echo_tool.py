from __future__ import annotations

import asyncio


async def run(payload: dict | list | str | None) -> dict:
    """Async sample tool that waits briefly and returns the payload."""
    await asyncio.sleep(0.01)
    return {"tool": "async_echo", "received": payload}
