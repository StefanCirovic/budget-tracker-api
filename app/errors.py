import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.errors import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "
VALIDATION_ERROR_MESSAGE = "The request contains invalid data."

HTTP_ERROR_CODES = {
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
}


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "not_found", message)


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "conflict", message)


class InvalidInputError(AppError):
    def __init__(self, location: str, field: str, message: str) -> None:
        detail = ErrorDetail(location=location, field=field, message=message)
        super().__init__(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "validation_error",
            VALIDATION_ERROR_MESSAGE,
            [detail],
        )


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details or []))
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


def validation_detail(error: dict) -> ErrorDetail:
    location, *path = error["loc"]
    if error["type"] == "json_invalid":
        return ErrorDetail(location=location, field=None, message="Request body is not valid JSON.")
    message = error["msg"].removeprefix(PYDANTIC_VALUE_ERROR_PREFIX)
    field = ".".join(str(part) for part in path) or None
    return ErrorDetail(location=location, field=field, message=message)


def http_error_message(request: Request, exc: StarletteHTTPException) -> str:
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return f"Path {request.url.path} does not exist."
    if exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return f"Method {request.method} is not allowed for path {request.url.path}."
    return str(exc.detail)


async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message, exc.details)


async def handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [validation_detail(error) for error in exc.errors()]
    return error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "validation_error",
        VALIDATION_ERROR_MESSAGE,
        details,
    )


async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = HTTP_ERROR_CODES.get(exc.status_code, "http_error")
    return error_response(exc.status_code, code, http_error_message(request, exc), headers=exc.headers)


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
    return error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "An unexpected error occurred.",
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
