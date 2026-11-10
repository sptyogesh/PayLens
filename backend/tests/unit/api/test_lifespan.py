from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def test_startup_sync_runs_only_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []
    monkeypatch.setattr("app.main.Base.metadata.create_all", lambda _engine: None)
    monkeypatch.setattr("app.main.start_startup_sync_thread", lambda *args: calls.append(args))
    with TestClient(create_app()):
        pass
    assert calls == []
    monkeypatch.setenv("STARTUP_SYNC_ENABLED", "true")
    from app.config import get_settings  # noqa: PLC0415

    get_settings.cache_clear()
    with TestClient(create_app()):
        pass
    assert len(calls) == 1
