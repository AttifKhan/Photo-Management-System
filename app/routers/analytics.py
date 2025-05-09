# Analytics dashboard route
# app/routers/analytics.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.engine import get_db
from app.db.models import Photo, Follow
from app.schemas.analytics import AnalyticsOut
from app.routers.dependencies import get_current_user

router = APIRouter(tags=["analytics"], prefix="/analytics")

@router.get("/", response_model=AnalyticsOut)
async def get_analytics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Return analytics for the current user/photographer:
    - number of photos uploaded
    - number of followers
    - number of users followed
    - total downloads across all their photos
    """
    user_id = current_user.id

    total_photos = (
        db.query(func.count(Photo.id))
          .filter(Photo.user_id == user_id)
          .scalar()
        or 0
    )
    total_followers = (
        db.query(func.count(Follow.id))
          .filter(Follow.followee_id == user_id)
          .scalar()
        or 0
    )
    total_following = (
        db.query(func.count(Follow.id))
          .filter(Follow.follower_id == user_id)
          .scalar()
        or 0
    )
    total_downloads = (
        db.query(func.coalesce(func.sum(Photo.download_count), 0))
          .filter(Photo.user_id == user_id)
          .scalar()
    )

    return AnalyticsOut(
        total_photos=total_photos,
        total_followers=total_followers,
        total_following=total_following,
        total_downloads=total_downloads
    )
