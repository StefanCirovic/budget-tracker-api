import pytest
from fastapi.testclient import TestClient

FOOD_ID = 1
RENT_ID = 2


@pytest.fixture(autouse=True)
def categories(client: TestClient) -> None:
    for name in ["Food", "Rent"]:
        assert client.post("/categories", json={"name": name, "color": "#112233"}).status_code == 201


def test_put_creates_a_budget_and_second_put_changes_it(client: TestClient) -> None:
    created = client.put(f"/budgets/2026-10/{FOOD_ID}", json={"amount": "250.00"})
    changed = client.put(f"/budgets/2026-10/{FOOD_ID}", json={"amount": "300.50"})

    assert created.status_code == 201
    assert changed.status_code == 200
    assert client.get("/budgets/2026-10").json() == [{"category_id": FOOD_ID, "month": "2026-10", "amount": "300.50"}]


def test_delete_removes_the_budget(client: TestClient) -> None:
    client.put(f"/budgets/2026-10/{FOOD_ID}", json={"amount": "250.00"})

    response = client.delete(f"/budgets/2026-10/{FOOD_ID}")

    assert response.status_code == 204
    assert client.get("/budgets/2026-10").json() == []


def test_invalid_amount_is_rejected(client: TestClient) -> None:
    response = client.put(f"/budgets/2026-10/{FOOD_ID}", json={"amount": "0"})

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "amount"


@pytest.mark.parametrize("month", ["2026-13", "2026-1", "2026-10-01", "october"])
def test_invalid_month_is_rejected(client: TestClient, month: str) -> None:
    response = client.get(f"/budgets/{month}")

    assert response.status_code == 422
    assert response.json()["error"]["details"] == [
        {"location": "path", "field": "month", "message": "Month must be a valid month in the form YYYY-MM."}
    ]


def test_nonexistent_category_returns_404(client: TestClient) -> None:
    response = client.put("/budgets/2026-10/999", json={"amount": "250.00"})

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Category 999 not found."


def test_list_returns_only_budgets_of_the_month(client: TestClient) -> None:
    client.put(f"/budgets/2026-10/{RENT_ID}", json={"amount": "500.00"})
    client.put(f"/budgets/2026-10/{FOOD_ID}", json={"amount": "250.00"})
    client.put(f"/budgets/2026-11/{FOOD_ID}", json={"amount": "999.00"})

    budgets = client.get("/budgets/2026-10").json()

    assert [(budget["category_id"], budget["amount"]) for budget in budgets] == [(FOOD_ID, "250.00"), (RENT_ID, "500.00")]


def test_deleting_a_category_deletes_its_budgets(client: TestClient) -> None:
    client.put(f"/budgets/2026-10/{FOOD_ID}", json={"amount": "250.00"})
    client.put(f"/budgets/2026-10/{RENT_ID}", json={"amount": "500.00"})

    client.delete(f"/categories/{FOOD_ID}")

    assert [budget["category_id"] for budget in client.get("/budgets/2026-10").json()] == [RENT_ID]
