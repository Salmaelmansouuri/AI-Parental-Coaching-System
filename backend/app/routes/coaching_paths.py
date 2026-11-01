from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.database import get_database
from backend.app.models.child import Child
from backend.app.models.coach_evaluation import CoachEvaluation
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
from backend.app.schemas.coach_evaluation import (
    CoachEvaluationResponse,
)
from backend.app.schemas.coaching_path import (
    CoachingPathConclusion,
    CoachingPathCreate,
    CoachingPathResponse,
)


router = APIRouter(
    prefix="/coaching-paths",
    tags=["Coaching Paths"],
)


def ensure_parent(user: User) -> None:
    if user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Seul un parent peut gérer "
                "ses parcours de coaching."
            ),
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
    response_model=CoachingPathResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_coaching_path(
    path_data: CoachingPathCreate,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachingPath:
    ensure_parent(current_user)

    child = database.scalar(
        select(Child).where(
            Child.id == path_data.child_id,
            Child.parent_id == current_user.id,
        )
    )

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="L'enfant sélectionné est introuvable.",
        )

    coaching_path = CoachingPath(
        parent_id=current_user.id,
        child_id=child.id,
        trigger_message=path_data.trigger_message,
        status=CoachingPathStatus.OPEN,
    )

    database.add(coaching_path)
    database.flush()

    trigger_message = Message(
        path_id=coaching_path.id,
        sender=MessageSender.PARENT,
        message_type=MessageType.TRIGGER,
        content=path_data.trigger_message,
    )

    database.add(trigger_message)

    database.commit()
    database.refresh(coaching_path)

    return coaching_path


@router.get(
    "",
    response_model=list[CoachingPathResponse],
)
def list_coaching_paths(
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> list[CoachingPath]:
    ensure_parent(current_user)

    paths = database.scalars(
        select(CoachingPath)
        .where(
            CoachingPath.parent_id == current_user.id
        )
        .order_by(
            CoachingPath.created_at.desc()
        )
    ).all()

    return list(paths)


@router.get(
    "/{path_id}",
    response_model=CoachingPathResponse,
)
def get_coaching_path(
    path_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachingPath:
    ensure_parent(current_user)

    return get_parent_path(
        path_id=path_id,
        current_user=current_user,
        database=database,
    )


@router.patch(
    "/{path_id}/conclusion",
    response_model=CoachingPathResponse,
)
def conclude_coaching_path(
    path_id: int,
    conclusion_data: CoachingPathConclusion,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachingPath:
    ensure_parent(current_user)

    coaching_path = get_parent_path(
        path_id=path_id,
        current_user=current_user,
        database=database,
    )

    if (
        coaching_path.status
        == CoachingPathStatus.CANCELLED
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Un parcours annulé "
                "ne peut pas être conclu."
            ),
        )

    coaching_path.parent_conclusion = (
        conclusion_data.parent_conclusion
    )

    coaching_path.status = (
        CoachingPathStatus.WAITING_COACH_REVIEW
    )

    coaching_path.completed_at = (
        datetime.now(timezone.utc)
    )

    conclusion_message = Message(
        path_id=coaching_path.id,
        sender=MessageSender.PARENT,
        message_type=MessageType.CONCLUSION,
        content=conclusion_data.parent_conclusion,
    )

    database.add(conclusion_message)

    database.commit()
    database.refresh(coaching_path)

    return coaching_path


@router.patch(
    "/{path_id}/cancel",
    response_model=CoachingPathResponse,
)
def cancel_coaching_path(
    path_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachingPath:
    ensure_parent(current_user)

    coaching_path = get_parent_path(
        path_id=path_id,
        current_user=current_user,
        database=database,
    )

    if (
        coaching_path.status
        == CoachingPathStatus.COMPLETED
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Un parcours terminé "
                "ne peut pas être annulé."
            ),
        )

    coaching_path.status = (
        CoachingPathStatus.CANCELLED
    )

    coaching_path.completed_at = (
        datetime.now(timezone.utc)
    )

    database.commit()
    database.refresh(coaching_path)

    return coaching_path


@router.get(
    "/{path_id}/evaluation",
    response_model=CoachEvaluationResponse,
)
def get_parent_path_evaluation(
    path_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachEvaluation:
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
            detail="Parcours introuvable.",
        )

    evaluation = database.scalar(
        select(CoachEvaluation).where(
            CoachEvaluation.path_id == path_id,
        )
    )

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune évaluation disponible.",
        )

    return evaluation