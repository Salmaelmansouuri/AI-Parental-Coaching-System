from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.database import get_database
from backend.app.models.child import Child
from backend.app.models.user import User, UserRole
from backend.app.schemas.child import (
    ChildCreate,
    ChildResponse,
    ChildUpdate,
)


router = APIRouter(
    prefix="/children",
    tags=["Children"],
)


def ensure_parent(user: User) -> None:
    if user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul un parent peut gérer les profils enfants.",
        )


@router.post(
    "",
    response_model=ChildResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_child(
    child_data: ChildCreate,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> Child:
    ensure_parent(current_user)

    child = Child(
        parent_id=current_user.id,
        alias=child_data.alias,
        age=child_data.age,
        gender=child_data.gender,
        family_context=child_data.family_context,
        additional_information=child_data.additional_information,
    )

    database.add(child)
    database.commit()
    database.refresh(child)

    return child


@router.get(
    "",
    response_model=list[ChildResponse],
)
def list_children(
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> list[Child]:
    ensure_parent(current_user)

    children = database.scalars(
        select(Child)
        .where(Child.parent_id == current_user.id)
        .order_by(Child.created_at.desc())
    ).all()

    return list(children)


@router.get(
    "/{child_id}",
    response_model=ChildResponse,
)
def get_child(
    child_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> Child:
    ensure_parent(current_user)

    child = database.scalar(
        select(Child).where(
            Child.id == child_id,
            Child.parent_id == current_user.id,
        )
    )

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil enfant introuvable.",
        )

    return child


@router.patch(
    "/{child_id}",
    response_model=ChildResponse,
)
def update_child(
    child_id: int,
    child_data: ChildUpdate,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> Child:
    ensure_parent(current_user)

    child = database.scalar(
        select(Child).where(
            Child.id == child_id,
            Child.parent_id == current_user.id,
        )
    )

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil enfant introuvable.",
        )

    update_values = child_data.model_dump(exclude_unset=True)

    for field, value in update_values.items():
        setattr(child, field, value)

    database.commit()
    database.refresh(child)

    return child


@router.delete(
    "/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_child(
    child_id: int,
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> None:
    ensure_parent(current_user)

    child = database.scalar(
        select(Child).where(
            Child.id == child_id,
            Child.parent_id == current_user.id,
        )
    )

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil enfant introuvable.",
        )

    database.delete(child)
    database.commit()