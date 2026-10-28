import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.fields import Amount, CategoryReference, Description, TransactionType

TransactionDate = Annotated[datetime.date, Field(description="Date in the form YYYY-MM-DD.", examples=["2026-10-27"])]


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: TransactionType
    amount: Amount
    date: TransactionDate
    description: Description = None
    category_id: CategoryReference


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: TransactionType = None
    amount: Amount = None
    date: TransactionDate = None
    description: Description = None
    category_id: CategoryReference = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    type: TransactionType
    amount: Decimal = Field(examples=["12.50"])
    date: datetime.date = Field(examples=["2026-10-27"])
    description: str | None = Field(examples=["Lunch with friends"])
    category_id: int = Field(examples=[1])


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int = Field(description="Number of transactions that match the filters.", examples=[42])
    page: int = Field(examples=[1])
    size: int = Field(examples=[20])
    pages: int = Field(description="Number of pages for this size.", examples=[3])
