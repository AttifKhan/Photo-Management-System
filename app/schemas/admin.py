from pydantic import BaseModel, ConfigDict
from .base import BaseModelConfig

class AdminActionOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    detail: str
