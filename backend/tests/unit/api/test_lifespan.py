from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.services.startup_service import StartupJobs


def start_app(monkeypatch: pytest.MonkeyPatch, **env: str) -> list[StartupJobs]:
    calls: list[Any] = []
    monkeypatch.setattr("app.main.Base.metadata.create_all", lambda _engine: None)
    monkeypatch.setattr("app.main.start_startup_thread", lambda deps, jobs: calls.append(jobs))
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    with TestClient(create_app()):
        pass
    return calls


def test_no_startup_thread_when_both_jobs_are_off(monkeypatch: pytest.MonkeyPatch) -> None:
    assert start_app(monkeypatch) == []


def test_seed_is_off_by_default() -> None:
    assert get_settings().seed_demo_on_startup is False


@pytest.mark.parametrize(
    ("env", "jobs"),
    [
        ({"STARTUP_SYNC_ENABLED": "true"}, StartupJobs(seed_demo=False, sync=True)),
        ({"SEED_DEMO_ON_STARTUP": "true"}, StartupJobs(seed_demo=True, sync=False)),
        (
            {"STARTUP_SYNC_ENABLED": "true", "SEED_DEMO_ON_STARTUP": "true"},
            StartupJobs(seed_demo=True, sync=True),
        ),
    ],
)
def test_one_thread_runs_the_enabled_jobs(
    monkeypatch: pytest.MonkeyPatch, env: dict[str, str], jobs: StartupJobs
) -> None:
    assert start_app(monkeypatch, **env) == [jobs]


def test_tables_are_created_on_every_start(monkeypatch: pytest.MonkeyPatch) -> None:
    engines: list[Any] = []
    monkeypatch.setattr("app.main.Base.metadata.create_all", engines.append)
    with TestClient(create_app()):
        pass
    assert len(engines) == 1
