from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9c8b51becd41"
down_revision: str | Sequence[str] | None = "43f6cdd1500f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("EXTRACT(DAY FROM month) = 1", name=op.f("ck_budgets_month_first_day")),
        sa.CheckConstraint("amount > 0 AND amount <= 1000000.00", name=op.f("ck_budgets_amount_range")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_budgets_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("category_id", "month", name=op.f("pk_budgets")),
    )


def downgrade() -> None:
    op.drop_table("budgets")
