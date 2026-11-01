from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.database import get_database
from backend.app.models.coach_evaluation import CoachEvaluation
from backend.app.models.coach_message_rating import CoachMessageRating
from backend.app.models.coaching_path import (
    CoachingPath,
    CoachingPathStatus,
)
from backend.app.models.message import Message, MessageSender
from backend.app.models.user import User, UserRole
from backend.app.schemas.coach_evaluation import (
    CoachEvaluationCreate,
    CoachEvaluationResponse,
)
from backend.app.schemas.coach_message_rating import (
    CoachMessageRatingResponse,
)
from backend.app.schemas.coaching_path import CoachingPathResponse
from backend.app.schemas.message import MessageResponse
from backend.app.schemas.rating import RatingCreate
from backend.app.services.ml_service import predict_path_evaluation


router = APIRouter(
    prefix="/coach",
    tags=["Human Coach"],
)


def ensure_coach(user: User) -> None:
    if user.role != UserRole.COACH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette action est réservée aux coachs humains.",
        )


def get_coaching_path_or_404(
    path_id: int,
    database: Session,
) -> CoachingPath:
    coaching_path = database.scalar(
        select(CoachingPath).where(
            CoachingPath.id == path_id,
        )
    )

    if not coaching_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcours de coaching introuvable.",
        )

    return coaching_path


def get_llm_message_for_coach(
    message_id: int,
    database: Session,
) -> Message:
    message = database.scalar(
        select(Message).where(
            Message.id == message_id,
        )
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message introuvable.",
        )

    get_coaching_path_or_404(
        path_id=message.path_id,
        database=database,
    )

    if message.sender != MessageSender.LLM:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Seules les réponses du coach IA "
                "peuvent recevoir une réaction du coach humain."
            ),
        )

    return message


@router.get(
    "/paths/pending",
    response_model=list[CoachingPathResponse],
)
def list_pending_paths(
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> list[CoachingPath]:
    ensure_coach(current_user)

    paths = database.scalars(
        select(CoachingPath)
        .where(
            CoachingPath.status
            == CoachingPathStatus.WAITING_COACH_REVIEW
        )
        .order_by(CoachingPath.completed_at.asc())
    ).all()

    return list(paths)


@router.get(
    "/paths/{path_id}",
    response_model=CoachingPathResponse,
)
def get_path_for_coach(
    path_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachingPath:
    ensure_coach(current_user)

    return get_coaching_path_or_404(
        path_id=path_id,
        database=database,
    )


@router.get(
    "/paths/{path_id}/messages",
    response_model=list[MessageResponse],
)
def get_path_messages_for_coach(
    path_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> list[Message]:
    ensure_coach(current_user)

    coaching_path = get_coaching_path_or_404(
        path_id=path_id,
        database=database,
    )

    messages = database.scalars(
        select(Message)
        .where(
            Message.path_id == coaching_path.id,
        )
        .order_by(Message.created_at.asc())
    ).all()

    return list(messages)


@router.put(
    "/messages/{message_id}/rating",
    response_model=CoachMessageRatingResponse,
)
def create_or_update_message_rating(
    message_id: int,
    rating_data: RatingCreate,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachMessageRating:
    ensure_coach(current_user)

    message = get_llm_message_for_coach(
        message_id=message_id,
        database=database,
    )

    rating = database.scalar(
        select(CoachMessageRating).where(
            CoachMessageRating.message_id == message.id,
            CoachMessageRating.coach_id == current_user.id,
        )
    )

    if rating:
        rating.value = rating_data.value

    else:
        rating = CoachMessageRating(
            message_id=message.id,
            coach_id=current_user.id,
            value=rating_data.value,
        )

        database.add(rating)

    database.commit()
    database.refresh(rating)

    return rating


@router.get(
    "/messages/{message_id}/rating",
    response_model=CoachMessageRatingResponse,
)
def get_message_rating_for_coach(
    message_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachMessageRating:
    ensure_coach(current_user)

    message = get_llm_message_for_coach(
        message_id=message_id,
        database=database,
    )

    rating = database.scalar(
        select(CoachMessageRating).where(
            CoachMessageRating.message_id == message.id,
            CoachMessageRating.coach_id == current_user.id,
        )
    )

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune réaction enregistrée pour ce message.",
        )

    return rating


@router.delete(
    "/messages/{message_id}/rating",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_message_rating_for_coach(
    message_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> None:
    ensure_coach(current_user)

    message = get_llm_message_for_coach(
        message_id=message_id,
        database=database,
    )

    rating = database.scalar(
        select(CoachMessageRating).where(
            CoachMessageRating.message_id == message.id,
            CoachMessageRating.coach_id == current_user.id,
        )
    )

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune réaction enregistrée pour ce message.",
        )

    database.delete(rating)
    database.commit()

@router.get(
    "/paths/{path_id}/ml-prediction",
)
def get_path_ml_prediction(
    path_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> dict:
    ensure_coach(current_user)

    get_coaching_path_or_404(
        path_id=path_id,
        database=database,
    )

    return predict_path_evaluation(
        database=database,
        path_id=path_id,
    )

@router.put(
    "/paths/{path_id}/evaluation",
    response_model=CoachEvaluationResponse,
)
def create_or_update_evaluation(
    path_id: int,
    evaluation_data: CoachEvaluationCreate,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachEvaluation:
    ensure_coach(current_user)

    coaching_path = get_coaching_path_or_404(
        path_id=path_id,
        database=database,
    )

    if coaching_path.status not in {
        CoachingPathStatus.WAITING_COACH_REVIEW,
        CoachingPathStatus.COMPLETED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Le parcours doit d'abord être conclu "
                "par le parent avant son évaluation."
            ),
        )

    global_score = round(
        (
            evaluation_data.relevance_score
            + evaluation_data.safety_score
            + evaluation_data.personalization_score
            + evaluation_data.document_fidelity_score
        )
        / 4,
        2,
    )

    evaluation = database.scalar(
        select(CoachEvaluation).where(
            CoachEvaluation.path_id == coaching_path.id,
        )
    )

    if evaluation:
        evaluation.coach_id = current_user.id
        evaluation.relevance_score = (
            evaluation_data.relevance_score
        )
        evaluation.safety_score = (
            evaluation_data.safety_score
        )
        evaluation.personalization_score = (
            evaluation_data.personalization_score
        )
        evaluation.document_fidelity_score = (
            evaluation_data.document_fidelity_score
        )
        evaluation.global_score = global_score
        evaluation.comment = evaluation_data.comment
        evaluation.validated = evaluation_data.validated

    else:
        evaluation = CoachEvaluation(
            path_id=coaching_path.id,
            coach_id=current_user.id,
            relevance_score=evaluation_data.relevance_score,
            safety_score=evaluation_data.safety_score,
            personalization_score=(
                evaluation_data.personalization_score
            ),
            document_fidelity_score=(
                evaluation_data.document_fidelity_score
            ),
            global_score=global_score,
            comment=evaluation_data.comment,
            validated=evaluation_data.validated,
        )

        database.add(evaluation)

    coaching_path.status = CoachingPathStatus.COMPLETED

    database.commit()
    database.refresh(evaluation)

    return evaluation


@router.get(
    "/paths/{path_id}/evaluation",
    response_model=CoachEvaluationResponse,
)
def get_path_evaluation(
    path_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachEvaluation:
    ensure_coach(current_user)

    get_coaching_path_or_404(
        path_id=path_id,
        database=database,
    )

    evaluation = database.scalar(
        select(CoachEvaluation).where(
            CoachEvaluation.path_id == path_id,
        )
    )

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune évaluation trouvée pour ce parcours.",
        )

    return evaluation