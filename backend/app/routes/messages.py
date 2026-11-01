from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.database import get_database
from backend.app.models.coaching_path import (
    CoachingPath,
    CoachingPathStatus,
)
from backend.app.models.message import (
    Message,
    MessageSender,
    MessageType,
)
from backend.app.models.user import User, UserRole
from backend.app.schemas.message import (
    MessageResponse,
    ParentMessageCreate,
)


router = APIRouter(
    prefix="/coaching-paths/{path_id}/messages",
    tags=["Messages"],
)


def ensure_parent(user: User) -> None:
    if user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette action est réservée aux parents.",
        )


def get_parent_path(
    path_id: int,
    current_user: User,
    database: Session,
) -> CoachingPath:
    coaching_path = database.scalar(
        select(CoachingPath).where(
            CoachingPath.id == path_id,
            CoachingPath.parent_id == current_user.id,
        )
    )

    if not coaching_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcours de coaching introuvable.",
        )

    return coaching_path


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_parent_message(
    path_id: int,
    message_data: ParentMessageCreate,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> Message:
    ensure_parent(current_user)

    coaching_path = get_parent_path(
        path_id=path_id,
        current_user=current_user,
        database=database,
    )

    if coaching_path.status in {
        CoachingPathStatus.COMPLETED,
        CoachingPathStatus.CANCELLED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Il est impossible d'ajouter un message "
                "à un parcours terminé ou annulé."
            ),
        )

    allowed_parent_types = {
        MessageType.PARENT_ANSWER,
        MessageType.FEEDBACK,
        MessageType.CONCLUSION,
    }

    if message_data.message_type not in allowed_parent_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Le parent peut uniquement envoyer une réponse, "
                "un retour ou une conclusion."
            ),
        )

    message = Message(
        path_id=coaching_path.id,
        sender=MessageSender.PARENT,
        message_type=message_data.message_type,
        content=message_data.content,
    )

    database.add(message)
    database.commit()
    database.refresh(message)

    return message


@router.get(
    "",
    response_model=list[MessageResponse],
)
def list_path_messages(
    path_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> list[Message]:
    ensure_parent(current_user)

    coaching_path = get_parent_path(
        path_id=path_id,
        current_user=current_user,
        database=database,
    )

    messages = database.scalars(
        select(Message)
        .where(Message.path_id == coaching_path.id)
        .order_by(Message.created_at.asc())
    ).all()

    return list(messages)