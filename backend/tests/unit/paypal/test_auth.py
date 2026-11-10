import httpx
import pytest
import respx

from app.common.errors import PayPalError
from app.common.http_client import make_client
from app.paypal import HttpPayPalGateway, TokenCache

BASE = "https://api-m.sandbox.paypal.com"


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def token(value: str, expires_in: int = 3600) -> httpx.Response:
    return httpx.Response(200, json={"access_token": value, "expires_in": expires_in})


@respx.mock
def test_p9_token_is_reused_until_refresh_margin() -> None:
    route = respx.post(f"{BASE}/v1/oauth2/token").mock(side_effect=[token("a"), token("b")])
    clock = FakeClock()
    cache = TokenCache(make_client(BASE), "id", "secret", clock)
    assert cache.get() == "a"
    clock.now = 3539.0
    assert cache.get() == "a"
    assert route.call_count == 1
    clock.now = 3540.0
    assert cache.get() == "b"
    assert route.call_count == 2


@respx.mock
def test_bad_credentials_raise_auth_failed() -> None:
    respx.post(f"{BASE}/v1/oauth2/token").mock(return_value=httpx.Response(401))
    with pytest.raises(PayPalError) as error:
        TokenCache(make_client(BASE), "id", "bad").get()
    assert error.value.code == "PAYPAL_AUTH_FAILED"


@respx.mock
def test_p5_401_refreshes_token_once_and_retries() -> None:
    respx.post(f"{BASE}/v1/oauth2/token").mock(side_effect=[token("old"), token("new")])
    api = respx.get(f"{BASE}/v1/thing").mock(
        side_effect=[httpx.Response(401), httpx.Response(200, json={})]
    )
    client = make_client(BASE)
    gateway = HttpPayPalGateway(client, TokenCache(client, "id", "secret"))
    assert gateway.request("GET", "/v1/thing").status_code == 200
    assert api.calls[1].request.headers["Authorization"] == "Bearer new"


@respx.mock
def test_second_401_raises_auth_failed() -> None:
    respx.post(f"{BASE}/v1/oauth2/token").mock(side_effect=[token("a"), token("b")])
    respx.get(f"{BASE}/v1/thing").mock(return_value=httpx.Response(401))
    client = make_client(BASE)
    gateway = HttpPayPalGateway(client, TokenCache(client, "id", "secret"))
    with pytest.raises(PayPalError) as error:
        gateway.request("GET", "/v1/thing")
    assert error.value.code == "PAYPAL_AUTH_FAILED"
