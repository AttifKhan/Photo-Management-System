from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from .base import BaseModelConfig

class CommentCreate(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    content: str = Field(..., min_length=1, max_length=500)

class CommentOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id:         int
    user_id:    int
    photo_id:   int
    content:    str
    created_at: datetime
