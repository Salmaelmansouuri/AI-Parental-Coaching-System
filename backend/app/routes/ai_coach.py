import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.database import get_database
from backend.app.models.child import Child
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
from backend.app.schemas.message import MessageResponse
from backend.app.services.rag_service import (
    build_aco_guidance,
    generate_parental_coach_response,
)


router = APIRouter(
    prefix="/coaching-paths",
    tags=["AI Coach"],
)


def ensure_parent(user: User) -> None:
    if user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette action est réservée aux parents.",
        )


@router.post(
    "/{path_id}/generate-response",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_ai_response(
    path_id: int,
    use_aco: bool = True,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> Message:
    ensure_parent(current_user)

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

    if coaching_path.status in {
        CoachingPathStatus.COMPLETED,
        CoachingPathStatus.CANCELLED,
        CoachingPathStatus.WAITING_COACH_REVIEW,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Le coach IA ne peut pas répondre dans un parcours "
                "terminé, annulé ou en attente d'évaluation."
            ),
        )

    child = database.scalar(
        select(Child).where(
            Child.id == coaching_path.child_id,
            Child.parent_id == current_user.id,
        )
    )

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil enfant introuvable.",
        )

    path_messages = database.scalars(
        select(Message)
        .where(Message.path_id == coaching_path.id)
        .order_by(Message.created_at.asc())
    ).all()

    messages_for_rag = [
        {
            "sender": message.sender.value,
            "message_type": message.message_type.value,
            "content": message.content,
        }
        for message in path_messages
    ]

    try:
        generated_response = generate_parental_coach_response(
            child_age=child.age,
            child_gender=child.gender.value,
            family_context=child.family_context,
            additional_information=child.additional_information,
            trigger_message=coaching_path.trigger_message,
            messages=messages_for_rag,
            use_aco=use_aco,
        )   

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur lors de la génération IA : {error}",
        ) from error

    generated_type = generated_response["message_type"]

    if generated_type == "question_clarification":
        message_type = MessageType.CLARIFICATION_QUESTION
        coaching_path.status = CoachingPathStatus.OPEN

    elif generated_type == "intervention":
        message_type = MessageType.INTERVENTION
        coaching_path.status = (
            CoachingPathStatus.WAITING_PARENT_FEEDBACK
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Type de réponse IA non reconnu.",
        )

    ai_message = Message(
    path_id=coaching_path.id,
    sender=MessageSender.LLM,
    message_type=message_type,
    content=generated_response["content"],
    sources_json=json.dumps(
        generated_response.get(
            "sources",
            [],
        ),
        ensure_ascii=False,
    ),
)

    database.add(ai_message)
    database.commit()
    database.refresh(ai_message)

    return ai_message
@router.get(
    "/{path_id}/aco-guidance"
)
def get_aco_guidance(
    path_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> dict:
    ensure_parent(current_user)

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

    path_messages = database.scalars(
        select(Message)
        .where(
            Message.path_id == coaching_path.id
        )
        .order_by(Message.created_at.asc())
    ).all()

    latest_parent_message = None

    for message in reversed(path_messages):
        if message.sender == MessageSender.PARENT:
            latest_parent_message = message.content
            break

    search_question = coaching_path.trigger_message

    if (
        latest_parent_message
        and latest_parent_message.strip()
        != coaching_path.trigger_message.strip()
    ):
        search_question = (
            coaching_path.trigger_message
            + " "
            + latest_parent_message
        )

    try:
        aco_result = build_aco_guidance(
            search_question
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur lors du calcul ACO : {error}",
        ) from error

    return {
        "path": aco_result["path"],
        "score": aco_result["score"],
        "intervention_scores": (
            aco_result["intervention_scores"]
        ),
    }