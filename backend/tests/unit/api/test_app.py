"""App-level API tests that need no database (lifespan is not started)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import create_app


class Body(BaseModel):
    amount: str


def make_app() -> FastAPI:
    app = create_app()

    @app.post("/_test/body")
    def body_route(body: Body) -> dict[str, str]:
        return {"amount": body.amount}

    @app.get("/_test/boom")
    def boom_route() -> None:
        raise RuntimeError("secret internal detail")

    return app


def test_a1_health() -> None:
    response = TestClient(make_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_a4_invalid_body_returns_422_standard_shape() -> None:
    response = TestClient(make_app()).post("/_test/body", json={"wrong": 1})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_a5_internal_error_is_safe() -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    response = client.get("/_test/boom")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "secret internal detail" not in response.text
    assert "Traceback" not in response.text


def test_a6_only_allowed_origins_get_cors_headers() -> None:
    client = TestClient(make_app())
    allowed = client.get("/health", headers={"Origin": "http://frontend.test"})
    local = client.get("/health", headers={"Origin": "http://localhost:3000"})
    blocked = client.get("/health", headers={"Origin": "https://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == "http://frontend.test"
    assert local.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in blocked.headers
