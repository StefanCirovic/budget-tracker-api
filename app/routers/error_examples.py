from app.routers.common import error_example, field_error, validation_example

CATEGORY_NOT_FOUND = error_example("not_found", "Category 999 not found.")

DUPLICATE_CATEGORY_NAME = error_example("conflict", "A category named 'Food' already exists.")

CATEGORY_HAS_TRANSACTIONS = error_example("conflict", "Category 1 has transactions and cannot be deleted.")

INVALID_CATEGORY_ID = validation_example(
    field_error("path", "category_id", "Input should be greater than or equal to 1"),
)

INVALID_CATEGORY_FIELDS = validation_example(
    field_error("body", "name", "Name must not be empty or contain only spaces."),
    field_error("body", "color", "Color must be a hex color in the form #RRGGBB."),
)

TRANSACTION_NOT_FOUND = error_example("not_found", "Transaction 999 not found.")

INVALID_TRANSACTION_ID = validation_example(
    field_error("path", "transaction_id", "Input should be greater than or equal to 1"),
)

INVALID_TRANSACTION_FIELDS = validation_example(
    field_error("body", "type", "Input should be 'income' or 'expense'"),
    field_error("body", "amount", "Input should be greater than 0"),
)

BUDGET_NOT_FOUND = error_example("not_found", "Category 1 has no budget for 2026-10.")

INVALID_MONTH = validation_example(
    field_error("path", "month", "Month must be a valid month in the form YYYY-MM."),
)

INVALID_BUDGET_AMOUNT = validation_example(
    field_error("body", "amount", "Input should be greater than 0"),
)

INVALID_TRANSACTION_FILTERS = validation_example(
    field_error("query", "date_from", "date_from must not be after date_to."),
)

INVALID_IMPORT_FILE = validation_example(
    field_error("body", "file", "Header must be exactly: type,amount,date,description,category."),
)
