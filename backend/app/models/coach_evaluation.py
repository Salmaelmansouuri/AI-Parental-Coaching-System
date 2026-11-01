from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class CoachEvaluation(Base):
    __tablename__ = "coach_evaluations"

    __table_args__ = (
        UniqueConstraint(
            "path_id",
            name="uq_coach_evaluation_path",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    path_id: Mapped[int] = mapped_column(
        ForeignKey(
            "coaching_paths.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    coach_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    relevance_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    safety_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    personalization_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    document_fidelity_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    global_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    validated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    coaching_path = relationship(
        "CoachingPath",
        back_populates="coach_evaluation",
    )

    coach = relationship(
        "User",
        back_populates="coach_evaluations",
    )