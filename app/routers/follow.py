# Follow/unfollow routes
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.engine import get_db
from app.db import crud
from app.routers.dependencies import get_current_user
from app.schemas.follow import FollowOut

router = APIRouter(tags=["follow"])

@router.post("/follow/{followee_id}", response_model=FollowOut)
def follow_user(
    followee_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Follow a photographer or user."""
    if current_user.id == followee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself"
        )
    # Check if followee exists
    followee = crud.get_user_by_id(db, followee_id)
    if not followee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Create follow relationship
    follow = crud.follow_user(db, current_user.id, followee_id)
    return FollowOut.from_orm(follow)

@router.delete("/follow/{followee_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    followee_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Unfollow a photographer or user."""
    crud.unfollow_user(db, current_user.id, followee_id)
    return None

@router.get("/followees", response_model=list[FollowOut])
def list_followees(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List users the current user is following."""
    follow_entries = db.query(crud.Follow).filter(crud.Follow.follower_id == current_user.id).all()
    return [FollowOut.model_validate(f) for f in follow_entries]
