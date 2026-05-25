from fastapi.testclient import TestClient

from app.main import app
from app.workers.reaper import reaper


def test_reaper_runs_during_lifespan():
    # ensure stopped before starting
    try:
        reaper.stop()
    except Exception:
        pass

    with TestClient(app) as client:
        # TestClient enters lifespan; reaper should have started
        assert reaper._thread is not None
        assert reaper._thread.is_alive()

    # after exiting context, reaper should stop
    assert not (reaper._thread and reaper._thread.is_alive())
