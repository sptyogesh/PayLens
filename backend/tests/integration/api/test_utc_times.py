"""Every time in API responses is UTC with Z, even when PostgreSQL returns local time."""

import re
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

UTC_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def times_in(value: Any, key: str = "") -> list[tuple[str, str]]:
    if isinstance(value, dict):
        return [t for k, v in value.items() for t in times_in(v, k)]
    if isinstance(value, list):
        return [t for item in value for t in times_in(item, key)]
    if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}T", value):
        return [(key, value)]
    return []


def test_all_api_times_are_utc_z_when_db_session_is_ist(
    api: TestClient, db_session: Session
) -> None:
    db_session.execute(text("SET TIME ZONE 'Asia/Kolkata'"))
    api.post("/sync")
    bodies = [
        api.get("/sync/last").json(),
        api.get("/transactions").json(),
        api.post("/sync").json(),
    ]
    times = [t for body in bodies for t in times_in(body)]
    keys = {key for key, _ in times}
    assert {"start", "end", "started_at", "finished_at", "occurred_at"} <= keys
    assert [t for t in times if not UTC_Z.match(t[1])] == []
