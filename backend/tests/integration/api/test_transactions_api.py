import re

from fastapi.testclient import TestClient

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
