from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import decode_access_token
from backend.app.database import get_database
from backend.app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    database: Session = Depends(get_database),
) -> User:
    email = decode_access_token(token)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Jeton invalide ou expiré.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not email:
        raise credentials_exception

    user = database.scalar(
        select(User).where(User.email == email)
    )

    if not user or not user.is_active:
        raise credentials_exception

    return user