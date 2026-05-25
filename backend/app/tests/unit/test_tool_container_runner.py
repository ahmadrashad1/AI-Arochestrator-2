from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace



def _load_tool_container_runner():
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "tool_container_runner.py"
    spec = importlib.util.spec_from_file_location("tool_container_runner", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _FakeTimes:
    def __init__(self, user: float, system: float):
        self.user = user
        self.system = system


class _FakeProcess:
    def __init__(self):
        self._count = 0

    def cpu_times(self):
        self._count += 1
        return _FakeTimes(user=float(self._count), system=float(self._count) / 2)

    def memory_info(self):
        return SimpleNamespace(rss=123456)


def test_tool_container_runner_reports_metrics(monkeypatch, capsys):
    tool_container_runner = _load_tool_container_runner()
    monkeypatch.setattr(tool_container_runner, "psutil", SimpleNamespace(Process=lambda: _FakeProcess()))
    monkeypatch.setattr(tool_container_runner, "_call_callable", lambda module, attr, payload: {"ok": True, "payload": payload})
    monkeypatch.setattr(tool_container_runner.sys, "stdin", io.StringIO(json.dumps({"module": "x", "attr": "run", "payload": {"a": 1}})))

    exit_code = tool_container_runner.main()
    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["cpu_seconds"] is not None
    assert out["memory_bytes"] == 123456
