import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.fields import Amount


class BudgetSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Amount


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int = Field(examples=[1])
    month: datetime.date = Field(examples=["2026-10"])
    amount: Decimal = Field(examples=["250.00"])

    @field_serializer("month")
    def format_month(self, month: datetime.date) -> str:
        return month.strftime("%Y-%m")
