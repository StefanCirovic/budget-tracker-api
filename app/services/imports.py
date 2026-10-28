import csv
import io
from collections.abc import Iterator
from typing import BinaryIO

from pydantic import ValidationError
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.errors import PYDANTIC_VALUE_ERROR_PREFIX, InvalidInputError
from app.models import Category, Transaction
from app.schemas.imports import ImportResult, ImportRowError
from app.schemas.transaction import TransactionCreate

CSV_COLUMNS = ["type", "amount", "date", "description", "category"]
MAX_ROWS = 1_000_000
BATCH_SIZE = 5_000
FIRST_DATA_ROW = 2


def file_error(message: str) -> InvalidInputError:
    return InvalidInputError("body", "file", message)


def category_ids_by_name(db: Session) -> dict[str, int]:
    return {name.lower(): category_id for category_id, name in db.execute(select(Category.id, Category.name))}


def validation_message(error: ValidationError) -> str:
    messages = []
    for detail in error.errors():
        field = ".".join(str(part) for part in detail["loc"])
        messages.append(f"{field}: {detail['msg'].removeprefix(PYDANTIC_VALUE_ERROR_PREFIX)}")
    return "; ".join(messages)


def parse_row(values: list[str], category_ids: dict[str, int]) -> dict:
    if len(values) != len(CSV_COLUMNS):
        raise ValueError(f"Row must have {len(CSV_COLUMNS)} columns.")
    row = dict(zip(CSV_COLUMNS, values))
    category_name = row.pop("category").strip()
    category_id = category_ids.get(category_name.lower())
    if category_id is None:
        raise ValueError(f"Category '{category_name}' does not exist.")
    try:
        return TransactionCreate(**row, category_id=category_id).model_dump()
    except ValidationError as error:
        raise ValueError(validation_message(error)) from None


def read_rows(file: BinaryIO) -> Iterator[list[str]]:
    text_file = io.TextIOWrapper(file, encoding="utf-8-sig", newline="")
    try:
        reader = csv.reader(text_file)
        header = next(reader, None)
        if header is None:
            raise file_error("File is empty.")
        if header != CSV_COLUMNS:
            raise file_error(f"Header must be exactly: {','.join(CSV_COLUMNS)}.")
        yield from reader
    finally:
        text_file.detach()


def count_data_rows(file: BinaryIO) -> int:
    return sum(1 for values in read_rows(file) if values)


def save_batch(db: Session, batch: list[dict]) -> None:
    if batch:
        db.execute(insert(Transaction), batch)
        batch.clear()


def import_rows(db: Session, file: BinaryIO) -> ImportResult:
    category_ids = category_ids_by_name(db)
    imported = 0
    errors = []
    batch = []
    for row_number, values in enumerate(read_rows(file), start=FIRST_DATA_ROW):
        if not values:
            continue
        try:
            batch.append(parse_row(values, category_ids))
        except ValueError as error:
            errors.append(ImportRowError(row=row_number, error=str(error)))
            continue
        imported += 1
        if len(batch) == BATCH_SIZE:
            save_batch(db, batch)
    save_batch(db, batch)
    db.commit()
    return ImportResult(imported=imported, failed=len(errors), errors=errors)


def import_transactions(db: Session, file: BinaryIO) -> ImportResult:
    try:
        if count_data_rows(file) > MAX_ROWS:
            raise file_error(f"File must have at most {MAX_ROWS} rows.")
        file.seek(0)
        return import_rows(db, file)
    except UnicodeDecodeError:
        raise file_error("File must be UTF-8 encoded text.") from None
    except csv.Error:
        raise file_error("File is not a valid CSV file.") from None
