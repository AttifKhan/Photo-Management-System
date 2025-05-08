from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.security import decode_access_token
from app.db.engine import get_db
from app.db import crud

# OAuth2 scheme to read token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Dependency to get the current authenticated user from JWT token.
    Raises 401 if invalid.
    """
    try:
        payload = decode_access_token(token)
        user_id: int = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def require_photographer(
    current_user = Depends(get_current_user)
):
    """
    Dependency to ensure the current user is a photographer.
    Raises 403 if not.
    """
    if not current_user.is_photographer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Photographer privileges required"
        )
    return current_user
