import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models import Budget, Category
from app.services.categories import get_category


def list_budgets(db: Session, month: datetime.date) -> list[Budget]:
    query = (
        select(Budget)
        .join(Category)
        .where(Budget.month == month)
        .order_by(func.lower(Category.name).collate("C"), Category.id)
    )
    return list(db.scalars(query))


def find_budget(db: Session, month: datetime.date, category_id: int) -> Budget | None:
    return db.get(Budget, {"category_id": category_id, "month": month})


def set_budget(db: Session, month: datetime.date, category_id: int, amount: Decimal) -> tuple[Budget, bool]:
    get_category(db, category_id)
    budget = find_budget(db, month, category_id)
    created = budget is None
    if created:
        budget = Budget(category_id=category_id, month=month, amount=amount)
        db.add(budget)
    else:
        budget.amount = amount
    db.commit()
    db.refresh(budget)
    return budget, created


def delete_budget(db: Session, month: datetime.date, category_id: int) -> None:
    get_category(db, category_id)
    budget = find_budget(db, month, category_id)
    if budget is None:
        raise NotFoundError(f"Category {category_id} has no budget for {month:%Y-%m}.")
    db.delete(budget)
    db.commit()
