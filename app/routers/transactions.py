import math
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.routers.common import DbSession
from app.routers.error_examples import (
    INVALID_TRANSACTION_FIELDS,
    INVALID_TRANSACTION_FILTERS,
    INVALID_TRANSACTION_ID,
    TRANSACTION_NOT_FOUND,
)
from app.schemas.fields import MAX_BIGINT_ID, MAX_INTEGER_ID, CategoryReference, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionPage, TransactionRead, TransactionUpdate
from app.services import transactions as transaction_service
from app.services.transactions import TransactionFilters

router = APIRouter(prefix="/transactions", tags=["Transactions"])

TransactionId = Annotated[int, Path(ge=1, le=MAX_BIGINT_ID, description="Id of the transaction.")]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TransactionRead,
    summary="Create a transaction",
    description=(
        "Records an income or an expense. The amount must be greater than 0, have at most 2 decimals "
        "and be at most 1000000.00. The date must be a valid date in the form YYYY-MM-DD. "
        "The description is optional, up to 200 characters. The category must exist."
    ),
    responses={422: INVALID_TRANSACTION_FIELDS},
)
def create_transaction(data: TransactionCreate, db: DbSession) -> TransactionRead:
    return transaction_service.create_transaction(db, data)


@router.get(
    "",
    response_model=TransactionPage,
    summary="List transactions",
    description=(
        "Returns transactions newest first; on the same date the one added last comes first. "
        "The result is split into pages. All filters are optional and can be combined: "
        "a date range (both ends included), a category, a type and a text that the description must contain, "
        "ignoring upper and lower case."
    ),
    responses={422: INVALID_TRANSACTION_FILTERS},
)
def list_transactions(
    db: DbSession,
    page: Annotated[int, Query(ge=1, le=MAX_INTEGER_ID, description="Page number, starting at 1.")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Number of transactions per page, 1 to 100.")] = 20,
    date_from: Annotated[date | None, Query(description="Only transactions on or after this date.")] = None,
    date_to: Annotated[date | None, Query(description="Only transactions on or before this date.")] = None,
    category_id: Annotated[CategoryReference | None, Query(description="Only transactions in this category.")] = None,
    transaction_type: Annotated[
        TransactionType | None, Query(alias="type", description="Only income or only expense.")
    ] = None,
    search: Annotated[str | None, Query(description="Only transactions whose description contains this text.")] = None,
) -> TransactionPage:
    filters = TransactionFilters(date_from, date_to, category_id, transaction_type, search)
    items, total = transaction_service.list_transactions(db, filters, page, size)
    return TransactionPage(items=items, total=total, page=page, size=size, pages=math.ceil(total / size))


@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Get a transaction",
    description="Returns one transaction by its id.",
    responses={404: TRANSACTION_NOT_FOUND, 422: INVALID_TRANSACTION_ID},
)
def get_transaction(transaction_id: TransactionId, db: DbSession) -> TransactionRead:
    return transaction_service.get_transaction(db, transaction_id)


@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Change a transaction",
    description=(
        "Changes one or more fields. Send only the fields to change; at least one is required. "
        "The same rules as for creating apply. Only the description can be set to null."
    ),
    responses={404: TRANSACTION_NOT_FOUND, 422: INVALID_TRANSACTION_FIELDS},
)
def update_transaction(transaction_id: TransactionId, data: TransactionUpdate, db: DbSession) -> TransactionRead:
    return transaction_service.update_transaction(db, transaction_id, data)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction",
    description="Deletes a transaction.",
    responses={404: TRANSACTION_NOT_FOUND, 422: INVALID_TRANSACTION_ID},
)
def delete_transaction(transaction_id: TransactionId, db: DbSession) -> None:
    transaction_service.delete_transaction(db, transaction_id)
