from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c27c5c835794"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=30), nullable=False),
        sa.Column("color", sa.CHAR(length=7), nullable=False),
        sa.CheckConstraint("char_length(name) BETWEEN 1 AND 30", name=op.f("ck_categories_name_length")),
        sa.CheckConstraint("color ~ '^#[0-9A-F]{6}$'", name=op.f("ck_categories_color_format")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
    )
    op.create_index("uq_categories_name_lower", "categories", [sa.text("lower(name)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_categories_name_lower", table_name="categories")
    op.drop_table("categories")
