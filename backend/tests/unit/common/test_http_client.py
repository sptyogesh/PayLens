import httpx
import pytest
import respx

from app.common.errors import PayPalError
from app.common.http_client import backoff_delay, make_client, send_with_retry

BASE = "https://api.test"


def run(client: httpx.Client, delays: list[float]) -> httpx.Response:
    return send_with_retry(lambda: client.get("/x"), sleep=delays.append)


@respx.mock
def test_p4_429_then_200_succeeds_after_backoff() -> None:
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[httpx.Response(429), httpx.Response(200, json={"ok": True})]
    )
    delays: list[float] = []
    response = run(make_client(BASE), delays)
    assert response.status_code == 200
    assert route.call_count == 2
    assert delays == [1.0]


@respx.mock
def test_server_errors_exhaust_retries_and_raise() -> None:
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(500))
    delays: list[float] = []
    with pytest.raises(PayPalError) as error:
        run(make_client(BASE), delays)
    assert error.value.code == "PAYPAL_UNAVAILABLE"
    assert route.call_count == 4
    assert delays == [1.0, 2.0, 4.0]


@respx.mock
def test_other_4xx_is_not_retried() -> None:
    route = respx.get(f"{BASE}/x").mock(return_value=httpx.Response(400))
    assert run(make_client(BASE), []).status_code == 400
    assert route.call_count == 1


@respx.mock
def test_network_errors_are_retried() -> None:
    respx.get(f"{BASE}/x").mock(side_effect=[httpx.ConnectError("down"), httpx.Response(200)])
    assert run(make_client(BASE), []).status_code == 200


def test_backoff_doubles() -> None:
    assert [backoff_delay(n) for n in range(3)] == [1.0, 2.0, 4.0]
