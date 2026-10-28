import datetime
from dataclasses import dataclass

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app.errors import InvalidInputError, NotFoundError
from app.models import Category, Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


@dataclass(frozen=True)
class TransactionFilters:
    date_from: datetime.date | None = None
    date_to: datetime.date | None = None
    category_id: int | None = None
    type: str | None = None
    search: str | None = None


def escape_like_pattern(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def ensure_category_exists(db: Session, category_id: int, location: str) -> None:
    if db.get(Category, category_id) is None:
        raise InvalidInputError(location, "category_id", f"Category {category_id} does not exist.")


def filter_conditions(db: Session, filters: TransactionFilters) -> list[ColumnElement[bool]]:
    if filters.date_from is not None and filters.date_to is not None and filters.date_from > filters.date_to:
        raise InvalidInputError("query", "date_from", "date_from must not be after date_to.")
    conditions = []
    if filters.date_from is not None:
        conditions.append(Transaction.date >= filters.date_from)
    if filters.date_to is not None:
        conditions.append(Transaction.date <= filters.date_to)
    if filters.category_id is not None:
        ensure_category_exists(db, filters.category_id, "query")
        conditions.append(Transaction.category_id == filters.category_id)
    if filters.type is not None:
        conditions.append(Transaction.type == filters.type)
    if filters.search:
        pattern = f"%{escape_like_pattern(filters.search)}%"
        conditions.append(Transaction.description.ilike(pattern, escape="\\"))
    return conditions


def list_transactions(
    db: Session, filters: TransactionFilters, page: int, size: int
) -> tuple[list[Transaction], int]:
    conditions = filter_conditions(db, filters)
    total = db.scalar(select(func.count()).select_from(Transaction).where(*conditions))
    query = (
        select(Transaction)
        .where(*conditions)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(query)), total


def get_transaction(db: Session, transaction_id: int) -> Transaction:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise NotFoundError(f"Transaction {transaction_id} not found.")
    return transaction


def create_transaction(db: Session, data: TransactionCreate) -> Transaction:
    ensure_category_exists(db, data.category_id, "body")
    transaction = Transaction(**data.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def update_transaction(db: Session, transaction_id: int, data: TransactionUpdate) -> Transaction:
    transaction = get_transaction(db, transaction_id)
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes:
        ensure_category_exists(db, changes["category_id"], "body")
    for field, value in changes.items():
        setattr(transaction, field, value)
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, transaction_id: int) -> None:
    transaction = get_transaction(db, transaction_id)
    db.delete(transaction)
    db.commit()
