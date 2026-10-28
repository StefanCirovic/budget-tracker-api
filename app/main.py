from fastapi import FastAPI

from app.errors import register_error_handlers
from app.routers import budgets, categories, imports, summary, transactions

API_DESCRIPTION = (
    "REST API for a personal budget tracker. One user records income and expenses, "
    "sorts them into categories, sets a monthly budget per category and sees a monthly summary. "
    "All amounts are in euros.\n\n"
    "Every error response has the same shape: "
    '`{"error": {"code": "...", "message": "...", "details": [...]}}`.'
)


def create_app() -> FastAPI:
    app = FastAPI(title="Budget Tracker API", version="1.0.0", description=API_DESCRIPTION)
    register_error_handlers(app)
    app.include_router(categories.router)
    app.include_router(transactions.router)
    app.include_router(budgets.router)
    app.include_router(summary.router)
    app.include_router(imports.router)
    return app


app = create_app()
