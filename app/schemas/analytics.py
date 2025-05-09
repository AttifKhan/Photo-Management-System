from pydantic import BaseModel, ConfigDict
from .base import BaseModelConfig

class AnalyticsOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    total_photos:    int
    total_followers: int
    total_following: int
    total_downloads: int
