from pydantic import BaseModel
from datetime import datetime


class FollowOut(BaseModel):
    id: int
    follower_id: int
    followee_id: int
    created_at: datetime

    class Config:
        orm_mode = True
