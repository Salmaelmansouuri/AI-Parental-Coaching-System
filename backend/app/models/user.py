from enum import Enum

from sqlalchemy import Boolean, Enum as SqlEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class UserRole(str, Enum):
    PARENT = "parent"
    COACH = "coach"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    ) 
    children = relationship(
        "Child",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    coaching_paths = relationship(
        "CoachingPath",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    ratings = relationship(
        "Rating",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    coach_evaluations = relationship(
        "CoachEvaluation",
        back_populates="coach",
        cascade="all, delete-orphan",
    )