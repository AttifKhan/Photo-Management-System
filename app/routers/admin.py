from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.engine import get_db
from app.db import crud
from app.db.models import User as UserModel, Photo as PhotoModel, Comment as CommentModel
from app.schemas.admin import AdminActionOut
from app.schemas.user import UserOut
from app.schemas.photo import PhotoListOut
from app.schemas.comment import CommentOut
from app.routers.dependencies import get_current_user

router = APIRouter(tags=["Admin"], prefix="/admin")

# Dependency to ensure admin user
def require_admin(current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """List all users (admin only)."""
    users = db.query(UserModel).all()
    return users

@router.delete("/users/{user_id}", response_model=AdminActionOut)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Delete a user and their content."""
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return AdminActionOut(detail=f"User {user_id} deleted")

@router.get("/photos", response_model=List[PhotoListOut])
def list_photos(
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """List all photo filenames (admin only)."""
    photos = db.query(PhotoModel).all()
    return photos

@router.delete("/photos/{photo_id}", response_model=AdminActionOut)
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Delete a photo."""
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    db.delete(photo)
    db.commit()
    return AdminActionOut(detail=f"Photo {photo_id} deleted")

@router.get("/comments", response_model=list[CommentOut])
def list_comments(
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """List all comment IDs (admin only)."""
    comments = db.query(CommentModel).all()
    return comments

@router.delete("/comments/{comment_id}", response_model=AdminActionOut)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Delete a comment."""
    comment = crud.get_comments_by_photo(db, comment_id)
    # Actually fetch single comment
    comment_obj = db.query(CommentModel).filter(CommentModel.id == comment_id).first()
    if not comment_obj:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(comment_obj)
    db.commit()
    return AdminActionOut(detail=f"Comment {comment_id} deleted")
