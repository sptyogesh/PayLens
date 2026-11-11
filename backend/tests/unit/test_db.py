import pytest

from app import db


def test_engine_disables_server_side_prepared_statements(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_engine(url: str, **kwargs: object) -> object:
        captured.update(kwargs, url=url)
        return object()

    monkeypatch.setattr(db, "create_engine", fake_create_engine)
    db.get_engine.cache_clear()
    try:
        db.get_engine()
    finally:
        db.get_engine.cache_clear()
    assert captured["connect_args"] == {"prepare_threshold": None}
    assert captured["pool_pre_ping"] is True
