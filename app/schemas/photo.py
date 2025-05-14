from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import List, Optional
from datetime import datetime
from .base import BaseModelConfig

class TagSuggestion(BaseModel):
    """Response model for photo upload endpoint"""
    captions: List[str]
    suggestions: List[str]

class PhotoCreate(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    caption:       Optional[str] = Field(None, description="Photo caption")
    selected_tags: List[str]     = Field(..., description="Up to 5 tags selected by user")


class ShareLinkOut(BaseModel):
    # Accept either a string or a URL object
    share_url: str

    model_config = ConfigDict(
        from_attributes=True
    )
    
class CommentOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id: int
    user_id: int
    username: str  # Username of commenter
    content: str
    created_at: datetime

class PhotoOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id: int
    user_id: int
    username: str  # Username of photographer
    filename: str
    caption: Optional[str]
    upload_time: datetime
    download_count: int
    tags: List[str]
    average_rating: float
    rating_count: int
    comments: List[CommentOut]

    @classmethod
    def from_orm(cls, photo):
        # Calculate average rating
        avg_rating = 0.0
        rating_count = 0
        if photo.ratings:
            scores = [r.score for r in photo.ratings]
            rating_count = len(scores)
            avg_rating = sum(scores) / rating_count if rating_count > 0 else 0.0
        
        # Format comments with username
        comments_list = []
        if photo.comments:
            comments_list = [
                CommentOut(
                    id=comment.id,
                    user_id=comment.user_id,
                    username=comment.user.username,
                    content=comment.content,
                    created_at=comment.created_at
                )
                for comment in photo.comments
            ]
        
        return cls(
            id=photo.id,
            user_id=photo.user_id,
            username=photo.owner.username,
            filename=photo.filename,
            caption=photo.caption,
            upload_time=photo.upload_time,
            download_count=photo.download_count,
            tags=[tag.tag_text for tag in photo.tags],
            average_rating=round(avg_rating, 1),
            rating_count=rating_count,
            comments=comments_list
        )

class PhotoListOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    id : int
    filename: str
    
class PhotoList(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    items: List[PhotoOut]
    skip:  int
    limit: int

