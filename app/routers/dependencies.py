# Add this to your dependencies module (probably in app/core/deps.py)
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.db.engine import get_db
from app.db import crud
from app.core.security import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        cookie_authorization = request.cookies.get("access_token")
        if cookie_authorization and cookie_authorization.startswith("Bearer "):
            token = cookie_authorization.replace("Bearer ", "")
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
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
