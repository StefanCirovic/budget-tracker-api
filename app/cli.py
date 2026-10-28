import argparse
import csv
import datetime
import random
import sys
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Budget, Category, Transaction

SEED_CATEGORIES = {
    "Eating out": "#E67E22",
    "Rent": "#8E44AD",
    "Salary": "#27AE60",
    "Transport": "#2980B9",
    "Other": "#7F8C8D",
}

SEED_TRANSACTIONS = [
    ("income", "2500.00", "2026-09-01", "September salary", "Salary"),
    ("expense", "750.00", "2026-09-03", "September rent", "Rent"),
    ("expense", "42.30", "2026-09-12", None, "Eating out"),
    ("expense", "35.00", "2026-09-20", "Monthly bus pass", "Transport"),
    ("expense", "18.99", "2026-09-25", None, "Other"),
    ("income", "2500.00", "2026-10-01", "October salary", "Salary"),
    ("expense", "750.00", "2026-10-03", "October rent", "Rent"),
    ("expense", "150.00", "2026-10-10", "Birthday dinner", "Eating out"),
    ("expense", "85.50", "2026-10-18", None, "Eating out"),
    ("expense", "40.00", "2026-10-22", "Phone case", "Other"),
]

SEED_BUDGETS = [
    ("Eating out", "200.00"),
    ("Rent", "800.00"),
    ("Transport", "100.00"),
]

SEED_BUDGET_MONTH = datetime.date(2026, 10, 1)

CSV_COLUMNS = ["type", "amount", "date", "description", "category"]
CSV_START_DATE = datetime.date(2026, 1, 1)
CSV_DAYS = 365


def reset_data(db: Session) -> None:
    db.execute(text("TRUNCATE budgets, transactions, categories RESTART IDENTITY"))


def insert_seed_data(db: Session) -> None:
    categories = [Category(name=name, color=color) for name, color in SEED_CATEGORIES.items()]
    db.add_all(categories)
    db.flush()
    category_ids = {category.name: category.id for category in categories}
    db.add_all(
        Transaction(
            type=transaction_type,
            amount=Decimal(amount),
            date=datetime.date.fromisoformat(date),
            description=description,
            category_id=category_ids[category],
        )
        for transaction_type, amount, date, description, category in SEED_TRANSACTIONS
    )
    db.add_all(
        Budget(category_id=category_ids[category], month=SEED_BUDGET_MONTH, amount=Decimal(amount))
        for category, amount in SEED_BUDGETS
    )


def seed(reset: bool) -> int:
    with SessionLocal() as db:
        if reset:
            reset_data(db)
        elif db.scalar(select(Category.id).limit(1)) is not None:
            print("Database already has categories. Run 'python -m app.cli seed --reset' to replace all data.", file=sys.stderr)
            return 1
        insert_seed_data(db)
        db.commit()
    print(
        f"Inserted {len(SEED_CATEGORIES)} categories, {len(SEED_TRANSACTIONS)} transactions "
        f"and {len(SEED_BUDGETS)} budgets for {SEED_BUDGET_MONTH:%Y-%m}."
    )
    return 0


def random_csv_row() -> list[str]:
    category = random.choice(list(SEED_CATEGORIES))
    transaction_type = "income" if category == "Salary" else "expense"
    amount = f"{random.randint(100, 100000) / 100:.2f}"
    date = CSV_START_DATE + datetime.timedelta(days=random.randrange(CSV_DAYS))
    description = random.choice(["", "Card payment", "Cash", "Online order"])
    return [transaction_type, amount, date.isoformat(), description, category]


def generate_csv(path: str, rows: int) -> int:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_COLUMNS)
        for _ in range(rows):
            writer.writerow(random_csv_row())
    print(f"Wrote {rows} rows to {path}.")
    return 0


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Budget Tracker data commands.")
    commands = parser.add_subparsers(dest="command", required=True)

    seed_parser = commands.add_parser("seed", help="Fill the database with sample data.")
    seed_parser.add_argument("--reset", action="store_true", help="Delete all budgets, transactions and categories first.")

    csv_parser = commands.add_parser("generate-csv", help="Write a CSV file with valid transactions for import.")
    csv_parser.add_argument("path", help="Output CSV file path.")
    csv_parser.add_argument("--rows", type=positive_int, default=1_000_000, help="Number of data rows (default 1000000).")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "seed":
        return seed(args.reset)
    return generate_csv(args.path, args.rows)


if __name__ == "__main__":
    sys.exit(main())
