# Pydantic schemas for user
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    is_photographer: Optional[bool] = False


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_photographer: bool
    is_admin: bool
    created_at: Optional[str]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
