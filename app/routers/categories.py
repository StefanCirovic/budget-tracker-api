from typing import Annotated

from fastapi import APIRouter, Path, status

from app.routers.common import DbSession
from app.routers.error_examples import (
    CATEGORY_HAS_TRANSACTIONS,
    CATEGORY_NOT_FOUND,
    DUPLICATE_CATEGORY_NAME,
    INVALID_CATEGORY_FIELDS,
    INVALID_CATEGORY_ID,
)
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.fields import MAX_INTEGER_ID
from app.services import categories as category_service

router = APIRouter(prefix="/categories", tags=["Categories"])

CategoryId = Annotated[int, Path(ge=1, le=MAX_INTEGER_ID, description="Id of the category.")]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryRead,
    summary="Create a category",
    description=(
        "Creates a category with a name and a color. Spaces at the start and end of the name are removed. "
        "The name must have 1 to 30 characters and must not match an existing name, ignoring upper and lower case. "
        "The color must be in the form #RRGGBB and is stored in uppercase."
    ),
    responses={409: DUPLICATE_CATEGORY_NAME, 422: INVALID_CATEGORY_FIELDS},
)
def create_category(data: CategoryCreate, db: DbSession) -> CategoryRead:
    return category_service.create_category(db, data)


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="List all categories",
    description="Returns every category, sorted by name, ignoring upper and lower case.",
)
def list_categories(db: DbSession) -> list[CategoryRead]:
    return category_service.list_categories(db)


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Get a category",
    description="Returns one category by its id.",
    responses={404: CATEGORY_NOT_FOUND, 422: INVALID_CATEGORY_ID},
)
def get_category(category_id: CategoryId, db: DbSession) -> CategoryRead:
    return category_service.get_category(db, category_id)


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Change the name or color of a category",
    description=(
        "Changes the name, the color, or both. Send only the fields to change; at least one is required "
        "and null is not allowed. The same rules as for creating apply. A category can be renamed to its "
        "own name with different upper and lower case."
    ),
    responses={404: CATEGORY_NOT_FOUND, 409: DUPLICATE_CATEGORY_NAME, 422: INVALID_CATEGORY_FIELDS},
)
def update_category(category_id: CategoryId, data: CategoryUpdate, db: DbSession) -> CategoryRead:
    return category_service.update_category(db, category_id, data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
    description="Deletes a category. A category that has transactions cannot be deleted.",
    responses={404: CATEGORY_NOT_FOUND, 409: CATEGORY_HAS_TRANSACTIONS, 422: INVALID_CATEGORY_ID},
)
def delete_category(category_id: CategoryId, db: DbSession) -> None:
    category_service.delete_category(db, category_id)
