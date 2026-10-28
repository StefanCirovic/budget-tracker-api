import pytest
from fastapi.testclient import TestClient

FOOD_ID = 1
RENT_ID = 2
SALARY_ID = 3


@pytest.fixture(autouse=True)
def categories(client: TestClient) -> None:
    for name in ["Food", "Rent", "Salary"]:
        assert client.post("/categories", json={"name": name, "color": "#112233"}).status_code == 201


def add_transaction(
    client: TestClient,
    amount: str,
    category_id: int = FOOD_ID,
    transaction_type: str = "expense",
    date: str = "2026-10-15",
) -> None:
    body = {"type": transaction_type, "amount": amount, "date": date, "category_id": category_id}
    assert client.post("/transactions", json=body).status_code == 201


def set_budget(client: TestClient, amount: str, category_id: int = FOOD_ID, month: str = "2026-10") -> None:
    assert client.put(f"/budgets/{month}/{category_id}", json={"amount": amount}).status_code == 201


def summary(client: TestClient, month: str = "2026-10") -> dict:
    response = client.get(f"/summary/{month}")
    assert response.status_code == 200, response.text
    return response.json()


def test_empty_month_shows_zero_totals_and_no_categories(client: TestClient) -> None:
    assert summary(client) == {
        "month": "2026-10",
        "total_income": "0.00",
        "total_expense": "0.00",
        "balance": "0.00",
        "categories": [],
    }


def test_totals_and_negative_balance_without_income_only_categories(client: TestClient) -> None:
    add_transaction(client, "100.00", category_id=SALARY_ID, transaction_type="income")
    add_transaction(client, "100.25")
    add_transaction(client, "50.25", category_id=RENT_ID)

    result = summary(client)

    assert (result["total_income"], result["total_expense"], result["balance"]) == ("100.00", "150.50", "-50.50")
    assert [category["name"] for category in result["categories"]] == ["Food", "Rent"]


def test_over_budget_category_has_negative_left(client: TestClient) -> None:
    set_budget(client, "100.00")
    add_transaction(client, "120.00")

    assert summary(client)["categories"] == [
        {"category_id": FOOD_ID, "name": "Food", "spent": "120.00", "budget": "100.00", "left": "-20.00"}
    ]


def test_category_with_only_a_budget_has_zero_spent(client: TestClient) -> None:
    set_budget(client, "250.00")

    assert summary(client)["categories"] == [
        {"category_id": FOOD_ID, "name": "Food", "spent": "0.00", "budget": "250.00", "left": "250.00"}
    ]


def test_category_with_expense_and_no_budget_has_null_budget_and_left(client: TestClient) -> None:
    add_transaction(client, "30.00")

    assert summary(client)["categories"] == [
        {"category_id": FOOD_ID, "name": "Food", "spent": "30.00", "budget": None, "left": None}
    ]


def test_categories_are_sorted_by_highest_expense_then_by_name(client: TestClient) -> None:
    add_transaction(client, "50.00", category_id=RENT_ID)
    add_transaction(client, "50.00", category_id=FOOD_ID)
    add_transaction(client, "80.00", category_id=SALARY_ID)
    set_budget(client, "10.00", category_id=SALARY_ID, month="2026-11")

    names = [category["name"] for category in summary(client)["categories"]]

    assert names == ["Salary", "Food", "Rent"]


def test_transactions_and_budgets_of_other_months_are_not_counted(client: TestClient) -> None:
    add_transaction(client, "1.00", date="2026-09-30")
    add_transaction(client, "2.00", date="2026-10-01")
    add_transaction(client, "3.00", date="2026-10-31")
    add_transaction(client, "4.00", date="2026-11-01")
    set_budget(client, "500.00", category_id=RENT_ID, month="2026-11")

    result = summary(client)

    assert result["total_expense"] == "5.00"
    assert [category["spent"] for category in result["categories"]] == ["5.00"]
