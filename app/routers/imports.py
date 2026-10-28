from fastapi import APIRouter, UploadFile

from app.routers.common import DbSession
from app.routers.error_examples import INVALID_IMPORT_FILE
from app.schemas.imports import ImportResult
from app.services import imports as import_service

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post(
    "",
    response_model=ImportResult,
    summary="Import transactions from a CSV file",
    description=(
        "Uploads a UTF-8 CSV file with the header `type,amount,date,description,category`, for example:\n\n"
        "```\ntype,amount,date,description,category\n"
        "expense,12.50,2026-10-08,Lunch,Eating out\nincome,300.00,2026-10-09,,Other\n```\n\n"
        "The category is given by name and must already exist, ignoring upper and lower case. "
        "An empty description means there is no description. Every row follows the same rules as a transaction. "
        "Rows that break a rule are skipped and listed with their line number and the reason; "
        "the other rows are saved. A file can have up to 1,000,000 rows; a larger file is rejected "
        "and nothing is saved. An empty file, a file that is not UTF-8 or a wrong header is rejected."
    ),
    responses={422: INVALID_IMPORT_FILE},
)
def import_transactions(file: UploadFile, db: DbSession) -> ImportResult:
    return import_service.import_transactions(db, file.file)
