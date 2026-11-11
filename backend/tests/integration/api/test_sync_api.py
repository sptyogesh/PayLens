import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.config import get_settings
from app.services.sync_lock import sync_lock


def test_post_sync_returns_run_summary(api: TestClient) -> None:
    response = api.post("/sync", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "success"
    assert body["counts"] == {"added": 10, "updated": 0, "skipped": 2, "flagged": 0}
    assert body["windows"] == {"total": 3, "done": 3}
    assert body["error"] is None


def test_second_sync_updates_instead_of_adding(api: TestClient) -> None:
    api.post("/sync")
    body = api.post("/sync").json()
    assert body["counts"]["added"] == 0 and body["counts"]["updated"] == 10
    assert body["hint"] is None


def test_last_sync_is_null_then_latest(api: TestClient) -> None:
    assert api.get("/sync/last").json() is None
    run_id = api.post("/sync").json()["id"]
    assert api.get("/sync/last").json()["id"] == run_id


def test_sync_in_progress_returns_409(api: TestClient, db_engine: Engine) -> None:
    with sync_lock(db_engine):
        response = api.post("/sync")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SYNC_IN_PROGRESS"


def test_invalid_period_returns_400(api: TestClient) -> None:
    body = {"start": "2026-11-02T00:00:00Z", "end": "2026-11-01T00:00:00Z"}
    response = api.post("/sync", json=body)
    assert (response.status_code, response.json()["error"]["code"]) == (400, "INVALID_PERIOD")


def test_naive_dates_are_a_validation_error(api: TestClient) -> None:
    response = api.post("/sync", json={"start": "2026-11-01T00:00:00"})
    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_ERROR")


def test_fourth_sync_within_a_minute_is_rate_limited(api: TestClient) -> None:
    statuses = [api.post("/sync").status_code for _ in range(4)]
    assert statuses == [200, 200, 200, 429]
    limited = api.post("/sync")
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
    assert int(limited.headers["Retry-After"]) > 0


def test_rate_limit_can_be_switched_off_for_e2e(
    api: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()
    assert [api.post("/sync").status_code for _ in range(4)] == [200] * 4


def test_sync_start_older_than_three_years_is_400(api: TestClient) -> None:
    response = api.post("/sync", json={"start": "2020-01-01T00:00:00Z"})
    assert (response.status_code, response.json()["error"]["code"]) == (400, "INVALID_PERIOD")


def test_failed_sync_still_refreshes_and_keeps_its_error(
    api: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    refreshed: list[bool] = []

    def boom(*_args: object) -> None:
        raise RuntimeError("sync bug")

    monkeypatch.setattr("app.api.routes.sync.start_sync", boom)
    monkeypatch.setattr("app.api.routes.sync.safe_refresh", lambda *_a: refreshed.append(True))
    client = TestClient(api.app, raise_server_exceptions=False)
    response = client.post("/sync", json={})
    assert (response.status_code, response.json()["error"]["code"]) == (500, "INTERNAL_ERROR")
    assert refreshed == [True]
