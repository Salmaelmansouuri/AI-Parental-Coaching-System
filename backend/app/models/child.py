from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class ChildGender(str, Enum):
    BOY = "garçon"
    GIRL = "fille"
    OTHER = "autre"
    NOT_SPECIFIED = "non_précisé"


class Child(Base):
    __tablename__ = "children"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    parent_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    alias: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    gender: Mapped[ChildGender] = mapped_column(
        SqlEnum(ChildGender),
        nullable=False,
    )

    family_context: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    additional_information: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    parent = relationship(
        "User",
        back_populates="children",
    )
    coaching_paths = relationship(
        "CoachingPath",
        back_populates="child",
        cascade="all, delete-orphan",
    )