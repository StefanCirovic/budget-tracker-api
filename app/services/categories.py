from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError
from app.models import Category, Transaction
from app.schemas.category import CategoryCreate, CategoryUpdate

UNIQUE_NAME_INDEX = "uq_categories_name_lower"


def duplicate_name_error(name: str) -> ConflictError:
    return ConflictError(f"A category named '{name}' already exists.")


def list_categories(db: Session) -> list[Category]:
    query = select(Category).order_by(func.lower(Category.name).collate("C"), Category.id)
    return list(db.scalars(query))


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError(f"Category {category_id} not found.")
    return category


def ensure_name_is_free(db: Session, name: str, excluded_category_id: int | None = None) -> None:
    query = select(Category.id).where(func.lower(Category.name) == func.lower(name))
    if excluded_category_id is not None:
        query = query.where(Category.id != excluded_category_id)
    if db.scalar(query) is not None:
        raise duplicate_name_error(name)


def commit_category(db: Session, category: Category) -> Category:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if exc.orig is not None and exc.orig.diag.constraint_name == UNIQUE_NAME_INDEX:
            raise duplicate_name_error(category.name) from exc
        raise
    return category


def create_category(db: Session, data: CategoryCreate) -> Category:
    ensure_name_is_free(db, data.name)
    category = Category(name=data.name, color=data.color)
    db.add(category)
    return commit_category(db, category)


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes:
        ensure_name_is_free(db, changes["name"], excluded_category_id=category.id)
    for field, value in changes.items():
        setattr(category, field, value)
    return commit_category(db, category)


def ensure_category_has_no_transactions(db: Session, category: Category) -> None:
    query = select(Transaction.id).where(Transaction.category_id == category.id).limit(1)
    if db.scalar(query) is not None:
        raise ConflictError(f"Category {category.id} has transactions and cannot be deleted.")


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    ensure_category_has_no_transactions(db, category)
    db.delete(category)
    db.commit()
