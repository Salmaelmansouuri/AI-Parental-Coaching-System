from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.database import get_database
from backend.app.models.coaching_path import CoachingPath
from backend.app.models.message import Message, MessageSender
from backend.app.models.rating import Rating
from backend.app.models.user import User, UserRole
from backend.app.schemas.rating import RatingCreate, RatingResponse


router = APIRouter(
    prefix="/messages",
    tags=["Ratings"],
)


def ensure_parent(user: User) -> None:
    if user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette action est réservée aux parents.",
        )


def get_parent_llm_message(
    message_id: int,
    current_user: User,
    database: Session,
) -> Message:
    message = database.scalar(
        select(Message)
        .join(
            CoachingPath,
            Message.path_id == CoachingPath.id,
        )
        .where(
            Message.id == message_id,
            CoachingPath.parent_id == current_user.id,
        )
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message introuvable.",
        )

    if message.sender != MessageSender.LLM:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Seules les réponses du coach IA "
                "peuvent recevoir un feedback."
            ),
        )

    return message


@router.put(
    "/{message_id}/rating",
    response_model=RatingResponse,
)
def create_or_update_rating(
    message_id: int,
    rating_data: RatingCreate,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> Rating:
    ensure_parent(current_user)

    message = get_parent_llm_message(
        message_id=message_id,
        current_user=current_user,
        database=database,
    )

    rating = database.scalar(
        select(Rating).where(
            Rating.message_id == message.id,
            Rating.parent_id == current_user.id,
        )
    )

    if rating:
        rating.value = rating_data.value
        rating.comment = rating_data.comment

    else:
        rating = Rating(
            message_id=message.id,
            parent_id=current_user.id,
            value=rating_data.value,
            comment=rating_data.comment,
        )

        database.add(rating)

    database.commit()
    database.refresh(rating)

    return rating


@router.get(
    "/{message_id}/rating",
    response_model=RatingResponse,
)
def get_message_rating(
    message_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> Rating:
    ensure_parent(current_user)

    message = get_parent_llm_message(
        message_id=message_id,
        current_user=current_user,
        database=database,
    )

    rating = database.scalar(
        select(Rating).where(
            Rating.message_id == message.id,
            Rating.parent_id == current_user.id,
        )
    )

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun feedback enregistré pour ce message.",
        )

    return rating


@router.delete(
    "/{message_id}/rating",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_message_rating(
    message_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> None:
    ensure_parent(current_user)

    message = get_parent_llm_message(
        message_id=message_id,
        current_user=current_user,
        database=database,
    )

    rating = database.scalar(
        select(Rating).where(
            Rating.message_id == message.id,
            Rating.parent_id == current_user.id,
        )
    )

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun feedback enregistré pour ce message.",
        )

    database.delete(rating)
    database.commit()