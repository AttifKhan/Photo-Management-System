from pydantic import BaseModel, ConfigDict
from typing import List
from .photo import PhotoOut
from .base import BaseModelConfig

class SearchResult(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    items: List[PhotoOut]
    skip:  int
    limit: int
