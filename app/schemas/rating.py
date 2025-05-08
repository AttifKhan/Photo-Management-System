# Pydantic schemas for rating
from pydantic import BaseModel, Field
from datetime import datetime


class RatingCreate(BaseModel):
    score: int = Field(..., ge=1, le=5, description="Rating score between 1 and 5")


class RatingOut(BaseModel):
    id: int
    user_id: int
    photo_id: int
    score: int
    created_at: datetime

    class Config:
        orm_mode = True
