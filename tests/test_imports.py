import pytest
from fastapi.testclient import TestClient

from app.services import imports

HEADER = "type,amount,date,description,category\n"


@pytest.fixture(autouse=True)
def categories(client: TestClient) -> None:
    for name in ["Eating out", "Other"]:
        assert client.post("/categories", json={"name": name, "color": "#112233"}).status_code == 201


def upload(client: TestClient, content: str) -> dict:
    response = client.post("/imports", files={"file": ("transactions.csv", content.encode(), "text/csv")})
    assert response.status_code == 200, response.text
    return response.json()


def saved_transactions(client: TestClient) -> list[dict]:
    return client.get("/transactions").json()["items"]


def test_example_from_the_task_is_imported(client: TestClient) -> None:
    content = HEADER + "expense,12.50,2026-10-08,Lunch,Eating out\nincome,300.00,2026-10-09,,Other\n"

    assert upload(client, content) == {"imported": 2, "failed": 0, "errors": []}
    assert [(item["type"], item["amount"]) for item in saved_transactions(client)] == [
        ("income", "300.00"),
        ("expense", "12.50"),
    ]


def test_category_is_found_ignoring_upper_and_lower_case(client: TestClient) -> None:
    upload(client, HEADER + "expense,5.00,2026-10-08,Coffee,EATING OUT\n")

    assert saved_transactions(client)[0]["category_id"] == 1


def test_empty_description_is_saved_as_null(client: TestClient) -> None:
    upload(client, HEADER + "income,300.00,2026-10-09,,Other\n")

    assert saved_transactions(client)[0]["description"] is None


def test_bad_rows_are_reported_and_good_rows_are_imported(client: TestClient) -> None:
    content = (
        HEADER
        + "expense,12.50,2026-10-08,Lunch,Eating out\n"
        + "expense,0,2026-10-08,Lunch,Eating out\n"
        + "expense,5.00,2026-10-08,Taxi,Xyz\n"
        + "expense,5.00,2026-10-08\n"
        + "\n"
    )

    assert upload(client, content) == {
        "imported": 1,
        "failed": 3,
        "errors": [
            {"row": 3, "error": "amount: Input should be greater than 0"},
            {"row": 4, "error": "Category 'Xyz' does not exist."},
            {"row": 5, "error": "Row must have 5 columns."},
        ],
    }
    assert len(saved_transactions(client)) == 1


def test_file_with_too_many_rows_is_rejected_and_nothing_is_saved(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(imports, "MAX_ROWS", 2)
    monkeypatch.setattr(imports, "BATCH_SIZE", 1)
    content = HEADER + "expense,1.00,2026-10-08,Lunch,Eating out\n" * 3
    files = {"file": ("transactions.csv", content.encode(), "text/csv")}

    response = client.post("/imports", files=files)

    assert response.status_code == 422
    assert response.json()["error"]["details"] == [
        {"location": "body", "field": "file", "message": "File must have at most 2 rows."}
    ]
    assert saved_transactions(client) == []


def test_wrong_header_is_rejected(client: TestClient) -> None:
    files = {"file": ("transactions.csv", b"kind,amount,date,description,category\n", "text/csv")}

    response = client.post("/imports", files=files)

    assert response.status_code == 422
    assert response.json()["error"]["details"] == [
        {
            "location": "body",
            "field": "file",
            "message": "Header must be exactly: type,amount,date,description,category.",
        }
    ]
