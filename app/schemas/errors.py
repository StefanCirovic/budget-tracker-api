from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    location: str | None = Field(description="Where the invalid value was sent: body, query or path.")
    field: str | None = Field(description="Name of the invalid field, or null when the error is not about one field.")
    message: str = Field(description="What is wrong with the value.")


class ErrorBody(BaseModel):
    code: str = Field(description="Machine readable error code.")
    message: str = Field(description="Human readable explanation.")
    details: list[ErrorDetail] = Field(description="Problems with individual fields. Empty when not applicable.")


class ErrorResponse(BaseModel):
    error: ErrorBody
