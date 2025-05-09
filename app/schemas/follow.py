from pydantic import BaseModel, ConfigDict
from datetime import datetime
from .base import BaseModelConfig

class FollowOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id:           int
    follower_id:  int
    followee_id:  int
    created_at:   datetime
