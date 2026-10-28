from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer


def format_money(value: Decimal) -> str:
    return f"{value:.2f}"


Money = Annotated[Decimal, PlainSerializer(format_money, return_type=str)]


class CategorySummary(BaseModel):
    category_id: int = Field(examples=[1])
    name: str = Field(examples=["Food"])
    spent: Money = Field(description="Total expense in the category this month.", examples=["120.00"])
    budget: Money | None = Field(description="Budget for the month, or null when none is set.", examples=["100.00"])
    left: Money | None = Field(
        description="Budget minus spent, negative when over budget; null when no budget is set.",
        examples=["-20.00"],
    )


class MonthSummary(BaseModel):
    month: str = Field(examples=["2026-10"])
    total_income: Money = Field(examples=["2000.00"])
    total_expense: Money = Field(examples=["1450.50"])
    balance: Money = Field(description="Income minus expense, can be negative.", examples=["549.50"])
    categories: list[CategorySummary]
