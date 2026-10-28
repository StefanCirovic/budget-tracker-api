import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, Field

MAX_INTEGER_ID = 2_147_483_647
MAX_BIGINT_ID = 9_223_372_036_854_775_807
CATEGORY_NAME_MAX_LENGTH = 30
DESCRIPTION_MAX_LENGTH = 200
COLOR_PATTERN = re.compile(r"#[0-9A-Fa-f]{6}")
MONTH_PATTERN = re.compile(r"[1-9][0-9]{3}-(0[1-9]|1[0-2])")


def normalize_category_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise ValueError("Name must not be empty or contain only spaces.")
    if len(name) > CATEGORY_NAME_MAX_LENGTH:
        raise ValueError(f"Name must be at most {CATEGORY_NAME_MAX_LENGTH} characters long.")
    return name


def normalize_color(value: str) -> str:
    if not COLOR_PATTERN.fullmatch(value):
        raise ValueError("Color must be a hex color in the form #RRGGBB.")
    return value.upper()


def normalize_description(value: str | None) -> str | None:
    if value is None:
        return None
    description = value.strip()
    if len(description) > DESCRIPTION_MAX_LENGTH:
        raise ValueError(f"Description must be at most {DESCRIPTION_MAX_LENGTH} characters long.")
    return description or None


def validate_month(value: str) -> str:
    if not MONTH_PATTERN.fullmatch(value):
        raise ValueError("Month must be a valid month in the form YYYY-MM.")
    return value


def first_day_of_month(month: str) -> date:
    return date.fromisoformat(f"{month}-01")


def first_day_of_next_month(month_start: date) -> date:
    return (month_start + timedelta(days=32)).replace(day=1)


CategoryName = Annotated[
    str,
    AfterValidator(normalize_category_name),
    Field(
        description=(
            "Category name. Spaces at the start and end are removed, then it must have 1 to 30 characters. "
            "Unique, ignoring upper and lower case."
        ),
        examples=["Eating out"],
        json_schema_extra={"minLength": 1, "maxLength": CATEGORY_NAME_MAX_LENGTH},
    ),
]

Color = Annotated[
    str,
    AfterValidator(normalize_color),
    Field(
        description="Hex color in the form #RRGGBB. Lowercase letters are accepted and stored as uppercase.",
        examples=["#FF8800"],
        json_schema_extra={"pattern": "^#[0-9A-Fa-f]{6}$"},
    ),
]

TransactionType = Annotated[
    Literal["income", "expense"],
    Field(description="Type of the transaction: income or expense.", examples=["expense"]),
]

Amount = Annotated[
    Decimal,
    Field(
        gt=0,
        le=Decimal("1000000.00"),
        decimal_places=2,
        description="Amount in euros. Greater than 0, at most 2 decimals, at most 1000000.00.",
        examples=["12.50"],
    ),
]

Description = Annotated[
    str | None,
    AfterValidator(normalize_description),
    Field(
        description=(
            "Optional text, up to 200 characters. Spaces at the start and end are removed; "
            "an empty description is stored as null."
        ),
        examples=["Lunch with friends"],
    ),
]

CategoryReference = Annotated[
    int,
    Field(ge=1, le=MAX_INTEGER_ID, description="Id of an existing category.", examples=[1]),
]
