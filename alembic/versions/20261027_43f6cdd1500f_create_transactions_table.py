from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "43f6cdd1500f"
down_revision: str | Sequence[str] | None = "c27c5c835794"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("type", sa.String(length=7), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("type IN ('income', 'expense')", name=op.f("ck_transactions_type_valid")),
        sa.CheckConstraint("amount > 0 AND amount <= 1000000.00", name=op.f("ck_transactions_amount_range")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_transactions_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])
    op.create_index("ix_transactions_date_id", "transactions", ["date", "id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_date_id", table_name="transactions")
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_table("transactions")
