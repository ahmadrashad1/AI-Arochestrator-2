"""Helper executed inside the container to run a tool and return JSON result.

Reads a JSON object from stdin with keys: module (str), attr (str), payload (any).
Executes the callable and prints a JSON envelope: {"ok": true, "result": ...} or {"ok": false, "error": "..."}
"""
from __future__ import annotations

import json
import sys
import time
import importlib
import asyncio
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
backend_root_str = str(backend_root)
if backend_root_str not in sys.path:
    sys.path.insert(0, backend_root_str)

try:
    import psutil
except Exception:
    psutil = None


def _call_callable(module: str, attr: str, payload):
    mod = importlib.import_module(module)
    target = getattr(mod, attr)
    if callable(target):
        # function or class
        if isinstance(target, type):
            inst = target()
            fn = getattr(inst, "run")
            if asyncio.iscoroutinefunction(fn):
                return asyncio.run(fn(payload))
            return fn(payload)
        else:
            if asyncio.iscoroutinefunction(target):
                return asyncio.run(target(payload))
            return target(payload)
    raise RuntimeError("target not callable")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"invalid input: {e}"}))
        return 1

    module = data.get("module")
    attr = data.get("attr")
    payload = data.get("payload")

    start = time.time()
    proc = psutil.Process() if psutil is not None else None
    cpu_before = None
    rss_before = None
    if proc is not None:
        try:
            cpu_before = proc.cpu_times()
            rss_before = proc.memory_info().rss
        except Exception:
            cpu_before = None
            rss_before = None

    try:
        res = _call_callable(module, attr, payload)
        ok = True
        err = None
    except Exception as e:
        res = None
        ok = False
        err = repr(e)

    duration = time.time() - start
    cpu_seconds = None
    mem_bytes = None
    if proc is not None:
        try:
            cpu_after = proc.cpu_times()
            rss_after = proc.memory_info().rss
            if cpu_before is not None:
                cpu_seconds = (cpu_after.user - cpu_before.user) + (cpu_after.system - cpu_before.system)
            mem_bytes = int(max(rss_before or 0, rss_after))
        except Exception:
            cpu_seconds = None
            mem_bytes = None

    out = {"ok": ok, "result": res if ok else None, "error": err, "duration": duration, "cpu_seconds": cpu_seconds, "memory_bytes": mem_bytes}
    print(json.dumps(out, default=str))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
