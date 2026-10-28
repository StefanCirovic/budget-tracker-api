import pytest
from fastapi.testclient import TestClient

FOOD_ID = 1
RENT_ID = 2


@pytest.fixture(autouse=True)
def categories(client: TestClient) -> None:
    for name in ["Food", "Rent"]:
        assert client.post("/categories", json={"name": name, "color": "#112233"}).status_code == 201


def transaction_body(**changes: object) -> dict:
    return {"type": "expense", "amount": "12.50", "date": "2026-10-27", "category_id": FOOD_ID} | changes


def create_transaction(client: TestClient, **changes: object) -> int:
    response = client.post("/transactions", json=transaction_body(**changes))
    assert response.status_code == 201, response.text
    return response.json()["id"]


def listed_ids(client: TestClient, **params: object) -> list[int]:
    response = client.get("/transactions", params=params)
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()["items"]]


def error_details(response) -> list[dict]:
    return response.json()["error"]["details"]


@pytest.mark.parametrize("amount", ["0.01", "1000000.00"])
def test_smallest_and_largest_amount_are_accepted(client: TestClient, amount: str) -> None:
    response = client.post("/transactions", json=transaction_body(amount=amount))

    assert response.status_code == 201
    assert response.json()["amount"] == amount


@pytest.mark.parametrize(
    ("amount", "message"),
    [
        ("0", "Input should be greater than 0"),
        ("-5.00", "Input should be greater than 0"),
        ("12.505", "Decimal input should have no more than 2 decimal places"),
        ("1000000.01", "Input should be less than or equal to 1000000.00"),
    ],
)
def test_invalid_amount_is_rejected(client: TestClient, amount: str, message: str) -> None:
    response = client.post("/transactions", json=transaction_body(amount=amount))

    assert response.status_code == 422
    assert error_details(response) == [{"location": "body", "field": "amount", "message": message}]


def test_invalid_date_is_rejected(client: TestClient) -> None:
    response = client.post("/transactions", json=transaction_body(date="2026-02-30"))

    assert response.status_code == 422
    assert error_details(response)[0]["field"] == "date"


def test_description_with_201_characters_is_rejected(client: TestClient) -> None:
    response = client.post("/transactions", json=transaction_body(description="D" * 201))

    assert response.status_code == 422
    assert error_details(response)[0]["field"] == "description"


def test_nonexistent_category_is_rejected(client: TestClient) -> None:
    response = client.post("/transactions", json=transaction_body(category_id=999))

    assert response.status_code == 422
    assert error_details(response) == [
        {"location": "body", "field": "category_id", "message": "Category 999 does not exist."}
    ]


def test_missing_transaction_returns_404(client: TestClient) -> None:
    response = client.get("/transactions/999")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Transaction 999 not found."


def test_list_is_newest_first_and_last_added_first_on_the_same_date(client: TestClient) -> None:
    older = create_transaction(client, date="2026-10-01")
    first_same_day = create_transaction(client, date="2026-10-05")
    second_same_day = create_transaction(client, date="2026-10-05")
    newest = create_transaction(client, date="2026-10-20")

    assert listed_ids(client) == [newest, second_same_day, first_same_day, older]


def test_pagination_returns_pages_and_total(client: TestClient) -> None:
    ids = [create_transaction(client, date=f"2026-10-0{day}") for day in range(1, 6)]

    first_page = client.get("/transactions", params={"page": 1, "size": 2}).json()
    second_page = client.get("/transactions", params={"page": 2, "size": 2}).json()

    assert [item["id"] for item in first_page["items"]] == [ids[4], ids[3]]
    assert [item["id"] for item in second_page["items"]] == [ids[2], ids[1]]
    assert (first_page["total"], first_page["pages"]) == (5, 3)


def test_all_filters_combined(client: TestClient) -> None:
    on_first_day = create_transaction(client, date="2026-10-10", description="DINNER at home")
    on_last_day = create_transaction(client, date="2026-10-20", description="Late dinner")
    create_transaction(client, date="2026-10-09", description="Dinner")
    create_transaction(client, date="2026-10-21", description="Dinner")
    create_transaction(client, date="2026-10-15", description="Dinner", category_id=RENT_ID)
    create_transaction(client, date="2026-10-15", description="Dinner", type="income")
    create_transaction(client, date="2026-10-15", description="Lunch")

    ids = listed_ids(
        client, date_from="2026-10-10", date_to="2026-10-20", category_id=FOOD_ID, type="expense", search="dinner"
    )

    assert ids == [on_last_day, on_first_day]


@pytest.mark.parametrize(
    ("params", "field", "message"),
    [
        ({"date_from": "2026-10-02", "date_to": "2026-10-01"}, "date_from", "date_from must not be after date_to."),
        ({"category_id": 999}, "category_id", "Category 999 does not exist."),
    ],
)
def test_invalid_filter_is_rejected(client: TestClient, params: dict, field: str, message: str) -> None:
    response = client.get("/transactions", params=params)

    assert response.status_code == 422
    assert error_details(response) == [{"location": "query", "field": field, "message": message}]


def test_category_with_transactions_cannot_be_deleted(client: TestClient) -> None:
    create_transaction(client, category_id=FOOD_ID)

    response = client.delete(f"/categories/{FOOD_ID}")

    assert response.status_code == 409
    assert client.get(f"/categories/{FOOD_ID}").status_code == 200
