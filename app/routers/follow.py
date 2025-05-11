# Follow/unfollow routes
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from pydantic import BaseModel

from app.db.engine import get_db
from app.db import crud
from app.routers.dependencies import get_current_user
from app.schemas.follow import FollowOut, FolloweesResponse, FollowersResponse

router = APIRouter(tags=["Follow"])

# New response models to include counts


@router.post("/follow/{photographer_id}", response_model=FollowOut)
def follow_photographer(
    photographer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Follow a photographer. Only photographers can be followed."""
    # Prevent following oneself
    if current_user.id == photographer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself"
        )
    
    # Check if photographer exists
    photographer = crud.get_user_by_id(db, photographer_id)
    if not photographer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Photographer not found"
        )
    
    # Check if the target user is a photographer
    if not photographer.is_photographer:  
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only follow photographers"
        )
    
    # Check if follow relationship already exists
    existing_follow = crud.get_follow(db, current_user.id, photographer_id)
    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already following this photographer"
        )
    
    # Create follow relationship
    follow = crud.follow_user(db, current_user.id, photographer_id)
    return FollowOut.from_orm(follow)

@router.delete("/follow/{photographer_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_photographer(
    photographer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Unfollow a photographer."""
    # Check if photographer exists
    photographer = crud.get_user_by_id(db, photographer_id)
    if not photographer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photographer not found"
        )
    
    # Check if the target user is a photographer
    if not photographer.is_photographer:  
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only follow/unfollow photographers"
        )
    
    # Check if follow relationship exists
    if not crud.check_follow_exists(db, current_user.id, photographer_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not following this photographer"
        )
    
    # Remove the follow relationship
    crud.unfollow_user(db, current_user.id, photographer_id)
    
    # For 204 responses, don't return anything
    return None

@router.get("/followees", response_model=FolloweesResponse)
def list_followees(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List photographers the current user is following with count."""
    follow_entries = db.query(crud.Follow).filter(crud.Follow.follower_id == current_user.id).all()
    followees_count = len(follow_entries)  
    
    return {
        "followees": [FollowOut.model_validate(f) for f in follow_entries],
        "count": followees_count
    }

@router.get("/followers", response_model=FollowersResponse)
def list_followers(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List users who are following the current photographer with count. Only accessible to photographers."""
    # Check if the current user is a photographer
    if not current_user.is_photographer:  # Assuming you have a field to identify photographers
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only photographers can view their followers"
        )
    
    follow_entries = db.query(crud.Follow).filter(crud.Follow.followee_id == current_user.id).all()
    followers_count = len(follow_entries)  # Count directly from the results
    
    return {
        "followers": [FollowOut.model_validate(f) for f in follow_entries],
        "count": followers_count
    }