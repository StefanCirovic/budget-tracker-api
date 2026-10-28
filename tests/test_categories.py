import pytest
from fastapi.testclient import TestClient


def create_category(client: TestClient, name: str = "Food", color: str = "#FF8800") -> dict:
    response = client.post("/categories", json={"name": name, "color": color})
    assert response.status_code == 201, response.text
    return response.json()


def error_messages(response) -> list[str]:
    return [detail["message"] for detail in response.json()["error"]["details"]]


@pytest.mark.parametrize("name", ["A", "N" * 30])
def test_name_with_1_or_30_characters_is_accepted(client: TestClient, name: str) -> None:
    assert create_category(client, name=name)["name"] == name


def test_name_with_31_characters_is_rejected(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "N" * 31, "color": "#000000"})

    assert response.status_code == 422
    assert error_messages(response) == ["Name must be at most 30 characters long."]


def test_name_is_trimmed(client: TestClient) -> None:
    assert create_category(client, name="  Eating out  ")["name"] == "Eating out"


def test_name_with_only_spaces_is_rejected(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "   ", "color": "#000000"})

    assert response.status_code == 422
    assert error_messages(response) == ["Name must not be empty or contain only spaces."]


def test_duplicate_name_with_different_case_is_rejected(client: TestClient) -> None:
    create_category(client, name="Food")

    response = client.post("/categories", json={"name": "fOOD", "color": "#000000"})

    assert response.status_code == 409
    assert response.json()["error"]["message"] == "A category named 'fOOD' already exists."


@pytest.mark.parametrize("color", ["#FFF", "FFFFFF", "#GGGGGG", "#FFFFFFF"])
def test_invalid_color_is_rejected(client: TestClient, color: str) -> None:
    response = client.post("/categories", json={"name": "Food", "color": color})

    assert response.status_code == 422
    assert error_messages(response) == ["Color must be a hex color in the form #RRGGBB."]


def test_lowercase_color_is_stored_in_uppercase(client: TestClient) -> None:
    assert create_category(client, color="#ff00aa")["color"] == "#FF00AA"


def test_list_is_sorted_by_name_ignoring_case(client: TestClient) -> None:
    for name in ["banana", "Cherry", "apple", "BLUEBERRY"]:
        create_category(client, name=name)

    names = [category["name"] for category in client.get("/categories").json()]

    assert names == ["apple", "banana", "BLUEBERRY", "Cherry"]


def test_missing_category_returns_404(client: TestClient) -> None:
    response = client.get("/categories/999")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Category 999 not found."
