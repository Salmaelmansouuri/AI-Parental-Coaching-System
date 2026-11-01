from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class CoachingPathStatus(str, Enum):
    OPEN = "ouvert"
    WAITING_PARENT_FEEDBACK = "en_attente_retour_parent"
    WAITING_COACH_REVIEW = "en_attente_evaluation_coach"
    COMPLETED = "termine"
    CANCELLED = "annule"


class CoachingPath(Base):
    __tablename__ = "coaching_paths"

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

    child_id: Mapped[int] = mapped_column(
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    trigger_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[CoachingPathStatus] = mapped_column(
        SqlEnum(CoachingPathStatus),
        default=CoachingPathStatus.OPEN,
        nullable=False,
    )

    parent_conclusion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    parent = relationship(
        "User",
        back_populates="coaching_paths",
    )

    child = relationship(
        "Child",
        back_populates="coaching_paths",
    )
    messages = relationship(
        "Message",
        back_populates="coaching_path",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    coach_evaluation = relationship(
        "CoachEvaluation",
        back_populates="coaching_path",
        cascade="all, delete-orphan",
        uselist=False,
    )