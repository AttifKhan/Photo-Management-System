from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List
from .base import BaseModelConfig

class FollowOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id:           int
    follower_id:  int
    followee_id:  int
    created_at:   datetime

class FolloweesResponse(BaseModel):
    followees: List[FollowOut]
    count: int

class FollowersResponse(BaseModel):
    followers: List[FollowOut]
    count: int