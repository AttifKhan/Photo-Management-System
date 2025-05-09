from pydantic import BaseModel, ConfigDict
from .base import BaseModelConfig

class SuggestionOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id:       int
    username: str
    score:    int
