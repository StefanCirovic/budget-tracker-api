# Budget Tracker API

A REST API for a single user to track income and expenses in euros. It manages categories, transactions and monthly budgets, imports transactions from CSV and shows a monthly summary.

Stack: Python 3.14, FastAPI, SQLAlchemy 2, PostgreSQL 18, Alembic, pytest.

## Run with Docker

```
docker compose up --build
```

The database starts first, the app applies migrations and the API is available at http://localhost:8000/docs.

```
docker compose down
docker compose down -v
```

`down` stops the containers and keeps the data. `down -v` also deletes the database volume.

## Run locally

Requires Python 3.14 and PostgreSQL with two databases: `budget_tracker` and `budget_tracker_test`.

```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

Create the two databases:

```
psql -U postgres -c "CREATE DATABASE budget_tracker;"
psql -U postgres -c "CREATE DATABASE budget_tracker_test;"
```

Copy `.env.example` to `.env` and set the password in `DATABASE_URL` and `TEST_DATABASE_URL`. Then:

```
alembic upgrade head
uvicorn app.main:app --reload
```

The API is available at http://localhost:8000/docs.

## Tests

```
pytest
```

Tests use the database from `TEST_DATABASE_URL`. They apply the migrations once and empty all tables before each test.

To run the tests in Docker without a local Python, start the containers, create the test database once and run pytest inside the app container:

```
docker compose exec db psql -U postgres -c "CREATE DATABASE budget_tracker_test;"
docker compose exec -e TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/budget_tracker_test app pytest
```

## Data command

```
python -m app.cli seed
python -m app.cli seed --reset
python -m app.cli generate-csv transactions.csv --rows 1000000
```

- `seed` fills an empty database with sample categories, transactions for September and October 2026 and budgets for October 2026, so `GET /summary/2026-10` shows every case. It refuses to run if categories already exist.
- `seed --reset` first deletes all data, then fills the database.
- `generate-csv` writes a CSV file with valid rows for testing a large import. It does not touch the database.

In Docker:

```
docker compose exec app python -m app.cli seed
```

## Data model

- `categories`: id, name (unique ignoring case), color.
- `transactions`: id, type, amount, date, description and `category_id`, a foreign key with `ON DELETE RESTRICT`, so a category with transactions can't be deleted.
- `budgets`: `category_id` + `month` as the primary key and an amount; the foreign key uses `ON DELETE CASCADE`, so deleting a category deletes its budgets.

## API

Interactive documentation is at `/docs` and the OpenAPI schema at `/openapi.json`. Every endpoint has its input, output and error examples there.

| Method | Path | Description |
|---|---|---|
| POST | `/categories` | Create a category |
| GET | `/categories` | List categories sorted by name |
| GET, PATCH, DELETE | `/categories/{category_id}` | Get, rename or recolor, delete a category |
| POST | `/transactions` | Create a transaction |
| GET | `/transactions` | List transactions, newest first, with pagination and filters |
| GET, PATCH, DELETE | `/transactions/{transaction_id}` | Get, update, delete a transaction |
| GET | `/budgets/{month}` | List budgets of a month |
| PUT, DELETE | `/budgets/{month}/{category_id}` | Set or change, remove a budget |
| GET | `/summary/{month}` | Monthly summary |
| POST | `/imports` | Import transactions from a CSV file |

`month` has the form `YYYY-MM`. Transaction list query parameters: `page`, `size`, `date_from`, `date_to`, `category_id`, `type`, `search`.

CSV import example:

```
curl -F "file=@transactions.csv" http://localhost:8000/imports
```

```json
{
  "imported": 2,
  "failed": 2,
  "errors": [
    {"row": 4, "error": "amount: Input should be greater than 0"},
    {"row": 5, "error": "Category 'Travel' does not exist."}
  ]
}
```

`row` is the line in the file, so the header is line 1.

Every error has the same format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request contains invalid data.",
    "details": [{"location": "body", "field": "amount", "message": "Input should be greater than 0"}]
  }
}
```

Codes: `validation_error` (422), `not_found` (404), `conflict` (409), `method_not_allowed` (405), `internal_error` (500).

## Assumptions and decisions

- In the summary, `budget` and `left` are `null` for a category with expenses but no budget, because a budget of 0 would mean planning to spend nothing, which is not the same as having no budget.
- A category with only income in a month is not listed in the summary, since the task asks for categories with an expense or a budget.
- `PUT /budgets/{month}/{category_id}` creates (201) or changes (200) a budget, because the month and the category together are its natural key.
- A nonexistent category in a transaction body or filter returns 422, because it is invalid input; in a budget path it returns 404, because the resource in the address doesn't exist.
- `date_from` after `date_to` returns 422 instead of an empty list, so a mistake in the filter is visible.
- Unknown fields in a request body are rejected with 422, so a typo in a field name doesn't get silently ignored.
- Colors are stored in uppercase, so `#ff0000` and `#FF0000` are the same color.
- Bad CSV rows are skipped and reported with their line number, while a problem with the whole file (wrong header, not UTF-8, too many rows) returns 422, because then the file itself breaks the rules.
- The CSV header must be exactly `type,amount,date,description,category`, so columns can't be mixed up.
- Empty lines in a CSV file are skipped, because editors often add one at the end.
- A file with more than 1,000,000 rows is rejected before anything is saved, because I count the rows first in a quick pass.
- `seed --reset` deletes all data and restarts ids from 1, so the sample data always looks the same.

