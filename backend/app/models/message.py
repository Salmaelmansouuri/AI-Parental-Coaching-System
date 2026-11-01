import json
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from backend.app.database import Base


class MessageSender(str, Enum):
    PARENT = "parent"
    LLM = "llm"
    COACH = "coach"
    SYSTEM = "system"


class MessageType(str, Enum):
    TRIGGER = "declencheur"
    CLARIFICATION_QUESTION = "question_clarification"
    PARENT_ANSWER = "reponse_parent"
    INTERVENTION = "intervention"
    FEEDBACK = "retour_parent"
    CONCLUSION = "conclusion"
    COACH_COMMENT = "commentaire_coach"


class Message(Base):
    __tablename__ = "messages"

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

    sender: Mapped[MessageSender] = mapped_column(
        SqlEnum(MessageSender),
        nullable=False,
    )

    message_type: Mapped[MessageType] = mapped_column(
        SqlEnum(MessageType),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sources_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    coaching_path = relationship(
        "CoachingPath",
        back_populates="messages",
    )

    ratings = relationship(
        "Rating",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    @property
    def sources(self) -> list[dict]:
        if not self.sources_json:
            return []

        try:
            parsed_sources = json.loads(
                self.sources_json
            )
        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return []

        if not isinstance(
            parsed_sources,
            list,
        ):
            return []

        return parsed_sources