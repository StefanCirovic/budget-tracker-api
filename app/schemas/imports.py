from pydantic import BaseModel, Field


class ImportRowError(BaseModel):
    row: int = Field(description="Line in the file; the header is line 1.", examples=[3])
    error: str = Field(examples=["amount: Input should be greater than 0"])


class ImportResult(BaseModel):
    imported: int = Field(description="Number of transactions that were saved.", examples=[2])
    failed: int = Field(description="Number of rows that were skipped.", examples=[1])
    errors: list[ImportRowError]
