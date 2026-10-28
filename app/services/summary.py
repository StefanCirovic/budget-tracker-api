import datetime
from decimal import Decimal

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import Session

from app.models import Budget, Category, Transaction
from app.schemas.fields import first_day_of_month, first_day_of_next_month
from app.schemas.summary import CategorySummary, MonthSummary


def transactions_in_month(month_start: datetime.date) -> list[ColumnElement[bool]]:
    return [Transaction.date >= month_start, Transaction.date < first_day_of_next_month(month_start)]


def total_of_type(transaction_type: str) -> ColumnElement[Decimal]:
    return func.coalesce(func.sum(Transaction.amount).filter(Transaction.type == transaction_type), 0)


def category_summaries(db: Session, month_start: datetime.date) -> list[CategorySummary]:
    spent = (
        select(Transaction.category_id, func.sum(Transaction.amount).label("spent"))
        .where(Transaction.type == "expense", *transactions_in_month(month_start))
        .group_by(Transaction.category_id)
        .subquery()
    )
    budget = select(Budget.category_id, Budget.amount).where(Budget.month == month_start).subquery()
    spent_or_zero = func.coalesce(spent.c.spent, 0)
    query = (
        select(Category.id, Category.name, spent_or_zero, budget.c.amount)
        .outerjoin(spent, spent.c.category_id == Category.id)
        .outerjoin(budget, budget.c.category_id == Category.id)
        .where(or_(spent.c.spent.is_not(None), budget.c.amount.is_not(None)))
        .order_by(spent_or_zero.desc(), func.lower(Category.name).collate("C"), Category.id)
    )
    return [
        CategorySummary(
            category_id=category_id,
            name=name,
            spent=spent_amount,
            budget=budget_amount,
            left=None if budget_amount is None else budget_amount - spent_amount,
        )
        for category_id, name, spent_amount, budget_amount in db.execute(query)
    ]


def month_summary(db: Session, month: str) -> MonthSummary:
    month_start = first_day_of_month(month)
    totals = select(total_of_type("income"), total_of_type("expense")).where(*transactions_in_month(month_start))
    income, expense = db.execute(totals).one()
    return MonthSummary(
        month=month,
        total_income=income,
        total_expense=expense,
        balance=income - expense,
        categories=category_summaries(db, month_start),
    )
