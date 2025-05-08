# Pydantic schemas for comment
from pydantic import BaseModel, Field
from datetime import datetime


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class CommentOut(BaseModel):
    id: int
    user_id: int
    photo_id: int
    content: str
    created_at: datetime

    class Config:
        orm_mode = True
