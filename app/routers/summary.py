from fastapi import APIRouter

from app.routers.common import DbSession, Month
from app.routers.error_examples import INVALID_MONTH
from app.schemas.summary import MonthSummary
from app.services import summary as summary_service

router = APIRouter(prefix="/summary", tags=["Summary"])


@router.get(
    "/{month}",
    response_model=MonthSummary,
    summary="Get the summary of a month",
    description=(
        "Returns total income, total expense and the balance (income minus expense, can be negative). "
        "Lists every category with an expense or a budget in the month: how much was spent, the budget "
        "and how much is left (budget minus spent, negative when over budget). Budget and left are null "
        "when the category has no budget. Highest expense first, then by name. "
        "A month with no transactions and no budgets shows zero totals and no categories."
    ),
    responses={422: INVALID_MONTH},
)
def get_summary(month: Month, db: DbSession) -> MonthSummary:
    return summary_service.month_summary(db, month)
