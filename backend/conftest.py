from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
backend_path = str(BACKEND_ROOT)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

REPO_ROOT = BACKEND_ROOT.parent
repo_path = str(REPO_ROOT)
if repo_path not in sys.path:
    sys.path.insert(0, repo_path)

import pytest

from app.database.repositories.base import reset_store


@pytest.fixture(autouse=True)
def _reset_in_memory_store() -> None:
    reset_store()