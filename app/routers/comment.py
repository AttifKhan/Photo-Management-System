# Comment routes
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

defender_module_import = None  # placeholder to maintain consistency

from app.db.engine import get_db
from app.db import crud
from app.schemas.comment import CommentCreate, CommentOut
from app.routers.dependencies import get_current_user

router = APIRouter(tags=["Comment"])

@router.post("/photos/{photo_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(photo_id: int, comment_in: CommentCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Post a comment on a photo.
    """
    # Ensure photo exists
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    # Create comment
    comment = crud.create_comment(db, user_id=current_user.id, photo_id=photo_id, content=comment_in.content)
    return comment

@router.get("/photos/{photo_id}/comments", response_model=list[CommentOut])
def list_comments(photo_id: int, db: Session = Depends(get_db)):
    """
    Retrieve comments for a given photo.
    """
    # Ensure photo exists
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    comments = crud.get_comments_by_photo(db, photo_id)
    return comments
