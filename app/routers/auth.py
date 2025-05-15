from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.engine import get_db
from app.db import crud
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserOut
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(tags=["Auth"])

@router.post(
    "/auth/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):

    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if crud.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pw = hash_password(user_in.password)
    user = crud.create_user(
        db,
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pw,
        is_photographer=user_in.is_photographer,
        is_admin=user_in.is_admin,
    )
    return user


@router.post(
    "/auth/login",
    response_model=Token,
    summary="Form-based login"
)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login using form-urlencoded data:
      Content-Type: application/x-www-form-urlencoded
      username=<email>&password=<password>
    """
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )    
    return {"access_token": access_token, "token_type": "bearer"}



