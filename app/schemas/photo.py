# Pydantic schemas for photo
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TagSuggestion(BaseModel):
    suggestions: List[str] = Field(..., description="AI suggested tags")


class PhotoCreate(BaseModel):
    caption: Optional[str] = Field(None, description="Photo caption")
    selected_tags: List[str] = Field(..., description="Up to 5 tags selected by user")


class PhotoOut(BaseModel):
    id: int
    user_id: int
    filename: str
    caption: Optional[str]
    upload_time: datetime
    download_count: int
    tags: List[str]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, photo):
        # Extract tag texts
        tag_texts = [tag.tag_text for tag in photo.tags]
        return cls(
            id=photo.id,
            user_id=photo.user_id,
            filename=photo.filename,
            caption=photo.caption,
            upload_time=photo.upload_time,
            download_count=photo.download_count,
            tags=tag_texts,
        )


class PhotoList(BaseModel):
    items: List[PhotoOut]
    skip: int
    limit: int

    class Config:
        orm_mode = True
