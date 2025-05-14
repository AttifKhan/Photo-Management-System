# Comment routes
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.engine import get_db
from app.db import crud
from app.schemas.comment import CommentCreate, CommentOut
from app.routers.dependencies import get_current_user

router = APIRouter(tags=["Comment"])

@router.post("/photos/{photo_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(photo_id: int, comment_in: CommentCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Post a comment on a photo.
    Only the photographer who posted the photo or users who follow that photographer can comment.
    """
 
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    

    is_photographer = photo.user_id == current_user.id
    follows_photographer = crud.check_follow_exists(db, follower_id=current_user.id, followee_id=photo.user_id)
    
    if not (is_photographer or follows_photographer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only comment on photos posted by photographers you follow or your own photos"
        )
    
    comment = crud.create_comment(db, user_id=current_user.id, photo_id=photo_id, content=comment_in.content)
    return comment

@router.get("/photos/{photo_id}/comments", response_model=list[CommentOut])
def list_comments(photo_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve comments for a given photo.
    Only the photographer who posted the photo or users who follow that photographer can view comments.
    """
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    

    is_photographer = photo.user_id == current_user.id
    follows_photographer = crud.check_follow_exists(db, follower_id=current_user.id, followee_id=photo.user_id)
    
    if not (is_photographer or follows_photographer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view comments on photos posted by photographers you follow or your own photos"
        )
    
    comments = crud.get_comments_by_photo(db, photo_id)
    return comments