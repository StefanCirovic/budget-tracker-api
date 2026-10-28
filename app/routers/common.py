from typing import Annotated, Any

from fastapi import Depends, Path
from pydantic import AfterValidator
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import VALIDATION_ERROR_MESSAGE
from app.schemas.errors import ErrorResponse
from app.schemas.fields import validate_month

DbSession = Annotated[Session, Depends(get_db)]

Month = Annotated[
    str,
    AfterValidator(validate_month),
    Path(description="Month in the form YYYY-MM.", examples=["2026-10"]),
]


def error_example(code: str, message: str, *details: dict[str, Any]) -> dict[str, Any]:
    body = {"error": {"code": code, "message": message, "details": list(details)}}
    return {"model": ErrorResponse, "content": {"application/json": {"example": body}}}


def validation_example(*details: dict[str, Any]) -> dict[str, Any]:
    return error_example("validation_error", VALIDATION_ERROR_MESSAGE, *details)


def field_error(location: str, field: str | None, message: str) -> dict[str, Any]:
    return {"location": location, "field": field, "message": message}
