from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import (
    create_access_token,
    verify_password,
)
from backend.app.database import get_database
from backend.app.models.user import User
from backend.app.schemas.auth import TokenResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    database: Session = Depends(get_database),
) -> TokenResponse:
    user = database.scalar(
        select(User).where(User.email == form_data.username)
    )

    if not user or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé.",
        )

    token = create_access_token(subject=user.email)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )