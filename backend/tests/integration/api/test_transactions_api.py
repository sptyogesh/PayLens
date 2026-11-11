import re

from fastapi.testclient import TestClient

from app.fakes.fx_fake import FakeFxGateway

MONEY = re.compile(r"^\d+\.\d{2}$")


def test_a3_every_row_has_source_and_string_money(api: TestClient) -> None:
    api.post("/sync")
    body = api.get("/transactions").json()
    assert body["total"] == 10
    for item in body["items"]:
        assert item["source"] == "paypal_sandbox"
        for field in ("gross", "fee", "net"):
            assert isinstance(item[field]["amount"], str)
            assert MONEY.match(item[field]["amount"])
        assert "raw_json" not in item and "flag_reason" not in item and "origin" not in item


def test_newest_first_and_paging(api: TestClient) -> None:
    api.post("/sync")
    items = api.get("/transactions", params={"limit": 3, "offset": 1}).json()["items"]
    dates = [item["occurred_at"] for item in items]
    assert len(items) == 3 and dates == sorted(dates, reverse=True)


def test_kind_all_includes_non_income_and_source_filter(api: TestClient) -> None:
    api.post("/sync")
    assert api.get("/transactions", params={"kind": "all"}).json()["total"] == 12
    assert api.get("/transactions", params={"source": "demo_seed"}).json()["total"] == 0


def test_invalid_query_is_422(api: TestClient) -> None:
    response = api.get("/transactions", params={"limit": 500})
    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_ERROR")


def test_leakage_fields_follow_the_contract(api: TestClient) -> None:
    api.post("/sync")
    items = api.get("/transactions").json()["items"]
    assert {item["leakage_status"] for item in items} == {"calculated"}
    leakage = items[0]["leakage"]
    assert leakage["paypal_rate_simulated"] is True
    assert re.match(r"^\d+\.\d{6}$", leakage["mid_market_rate"])
    assert leakage["total_leakage_inr"]["currency"] == "INR"
    assert MONEY.match(leakage["total_leakage_inr"]["amount"])
    assert re.match(r"^\d+\.\d{2}$", leakage["leakage_percent"])


def test_non_income_rows_are_not_applicable(api: TestClient) -> None:
    api.post("/sync")
    items = api.get("/transactions", params={"kind": "all"}).json()["items"]
    other = [item for item in items if item["kind"] != "income"]
    assert other and all(item["leakage_status"] == "not_applicable" for item in other)
    assert all(item["leakage"] is None for item in other)


def test_fx_outage_shows_rate_unavailable(api: TestClient, fake_fx: FakeFxGateway) -> None:
    fake_fx.unavailable = True
    assert api.post("/sync").status_code == 200
    items = api.get("/transactions").json()["items"]
    assert {item["leakage_status"] for item in items} == {"rate_unavailable"}
    assert all(item["leakage"] is None for item in items)
