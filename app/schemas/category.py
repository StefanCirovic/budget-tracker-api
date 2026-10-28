from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.fields import CategoryName, Color


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: CategoryName
    color: Color


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: CategoryName = None
    color: Color = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one of the fields name or color must be provided.")
        return self


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    name: str = Field(examples=["Eating out"])
    color: str = Field(examples=["#FF8800"])
