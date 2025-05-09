from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from .base import BaseModelConfig

class TagSuggestion(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    suggestions: List[str] = Field(..., description="AI suggested tags")

class PhotoCreate(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    caption:       Optional[str] = Field(None, description="Photo caption")
    selected_tags: List[str]     = Field(..., description="Up to 5 tags selected by user")

class PhotoOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id:             int
    user_id:        int
    filename:       str
    caption:        Optional[str]
    upload_time:    datetime
    download_count: int
    tags:           List[str]

    @classmethod
    def from_orm(cls, photo):
        return cls(
            id=photo.id,
            user_id=photo.user_id,
            filename=photo.filename,
            caption=photo.caption,
            upload_time=photo.upload_time,
            download_count=photo.download_count,
            tags=[t.tag_text for t in photo.tags],
        )

class PhotoList(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    items: List[PhotoOut]
    skip:  int
    limit: int
