from sqlalchemy import CHAR, CheckConstraint, Identity, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 30", name="name_length"),
        CheckConstraint("color ~ '^#[0-9A-F]{6}$'", name="color_format"),
        Index("uq_categories_name_lower", text("lower(name)"), unique=True),
    )

    id: Mapped[int] = mapped_column(Identity(always=False), primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    color: Mapped[str] = mapped_column(CHAR(7))
