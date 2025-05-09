from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from .base import BaseModelConfig

class RatingCreate(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    score: int = Field(..., ge=1, le=5, description="Rating score between 1 and 5")

class RatingOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id:         int
    user_id:    int
    photo_id:   int
    score:      int
    created_at: datetime

    @classmethod
    def from_orm(cls, rating):
        return cls(
            id=rating.id,
            user_id=rating.user_id,
            photo_id=rating.photo_id,
            score=rating.score,
            created_at=rating.created_at,
        )
