from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CheckpointStore:
    def __init__(self, base_dir: str | Path = ".checkpoints"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, workflow_id: str) -> Path:
        return self.base_dir / f"{workflow_id}.json"

    def save(self, workflow_id: str, state: dict[str, Any]) -> None:
        self._path_for(workflow_id).write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

    def load(self, workflow_id: str) -> dict[str, Any] | None:
        path = self._path_for(workflow_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, workflow_id: str) -> bool:
        return self._path_for(workflow_id).exists()
