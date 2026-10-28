from fastapi import APIRouter, Response, status

from app.routers.categories import CategoryId
from app.routers.common import DbSession, Month
from app.routers.error_examples import BUDGET_NOT_FOUND, CATEGORY_NOT_FOUND, INVALID_BUDGET_AMOUNT, INVALID_MONTH
from app.schemas.budget import BudgetRead, BudgetSet
from app.schemas.fields import first_day_of_month
from app.services import budgets as budget_service

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get(
    "/{month}",
    response_model=list[BudgetRead],
    summary="List the budgets of a month",
    description="Returns every budget set for the month, sorted by category name.",
    responses={422: INVALID_MONTH},
)
def list_budgets(month: Month, db: DbSession) -> list[BudgetRead]:
    return budget_service.list_budgets(db, first_day_of_month(month))


@router.put(
    "/{month}/{category_id}",
    response_model=BudgetRead,
    summary="Set or change the budget of a category for a month",
    description=(
        "Sets how much the user plans to spend in the category in the month. "
        "Returns 201 when the budget is new and 200 when an existing budget is changed. "
        "A category has at most one budget per month. The amount follows the same rules as a transaction amount."
    ),
    responses={
        status.HTTP_201_CREATED: {"model": BudgetRead, "description": "Budget created."},
        404: CATEGORY_NOT_FOUND,
        422: INVALID_BUDGET_AMOUNT,
    },
)
def set_budget(month: Month, category_id: CategoryId, data: BudgetSet, db: DbSession, response: Response) -> BudgetRead:
    budget, created = budget_service.set_budget(db, first_day_of_month(month), category_id, data.amount)
    if created:
        response.status_code = status.HTTP_201_CREATED
    return budget


@router.delete(
    "/{month}/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove the budget of a category for a month",
    description="Removes the budget. Returns 404 when the category or the budget does not exist.",
    responses={404: BUDGET_NOT_FOUND, 422: INVALID_MONTH},
)
def delete_budget(month: Month, category_id: CategoryId, db: DbSession) -> None:
    budget_service.delete_budget(db, first_day_of_month(month), category_id)
