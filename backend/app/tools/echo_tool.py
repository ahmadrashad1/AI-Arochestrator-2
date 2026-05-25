from __future__ import annotations

def run(payload: dict | list | str | None) -> dict:
    """A trivial sample tool that echoes the input back as structured output.

    Useful for local integration tests and as a reference implementation.
    """
    return {"tool": "echo", "received": payload}
