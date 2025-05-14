# Rating routes
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.engine import get_db
from app.db import crud
from app.schemas.rating import RatingCreate, RatingOut
from app.routers.dependencies import get_current_user
from app.db.models import Photo as PhotoModel

router = APIRouter(tags=["Rating"])

@router.post("/photos/{photo_id}/ratings", response_model=RatingOut, status_code=status.HTTP_201_CREATED)
def create_rating(
    photo_id: int,
    rating_in: RatingCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit a rating for a photo.
    Only the photographer who posted the photo or users who follow that photographer can rate.
    """
    # Ensure photo exists
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    
    # Check if user is the photographer who posted the photo
    is_photographer = photo.user_id == current_user.id
    
    # Check if user follows the photographer
    follows_photographer = crud.check_follow_exists(db, follower_id=current_user.id, followee_id=photo.user_id)
    
    # Verify permission
    if not (is_photographer or follows_photographer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only rate photos posted by photographers you follow or your own photos"
        )
    
    # Create rating
    rating = crud.create_rating(db, user_id=current_user.id, photo_id=photo_id, score=rating_in.score)
    return rating

@router.get("/photos/{photo_id}/ratings", response_model=List[RatingOut])
def list_ratings(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all ratings for a photo.
    Only the photographer who posted the photo or users who follow that photographer can view ratings.
    """
    # Ensure photo exists
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    
    # Check if user is the photographer who posted the photo
    is_photographer = photo.user_id == current_user.id
    
    # Check if user follows the photographer
    follows_photographer = crud.check_follow_exists(db, follower_id=current_user.id, followee_id=photo.user_id)
    
    # Verify permission
    if not (is_photographer or follows_photographer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view ratings on photos posted by photographers you follow or your own photos"
        )
    
    ratings = crud.get_ratings_by_photo(db, photo_id)
    return ratings

@router.get("/photos/{photo_id}/ratings/average", response_model=float)
def average_rating(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get average rating for a photo.
    Only the photographer who posted the photo or users who follow that photographer can view average rating.
    """
    # Ensure photo exists
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    
    # Check if user is the photographer who posted the photo
    is_photographer = photo.user_id == current_user.id
    
    # Check if user follows the photographer
    follows_photographer = crud.check_follow_exists(db, follower_id=current_user.id, followee_id=photo.user_id)
    
    # Verify permission
    if not (is_photographer or follows_photographer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view average ratings on photos posted by photographers you follow or your own photos"
        )
    
    avg = crud.get_average_rating(db, photo_id)
    return avg