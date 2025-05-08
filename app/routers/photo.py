import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.engine import get_db
from app.db import crud
from app.db.models import Photo as PhotoModel
from app.schemas.photo import PhotoCreate, PhotoOut, TagSuggestion, PhotoList
from app.routers.dependencies import get_current_user, require_photographer
from app.ai.predictor import suggest_tags

router = APIRouter(tags=["photo"])

# Directory to store uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "app/static/uploads")
# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/photos/upload", response_model=TagSuggestion)
async def upload_photo_for_tags(
    file: UploadFile = File(...),
    current_user = Depends(require_photographer)
):
    """
    Uploads photo temporarily to get AI tag suggestions.
    Returns top 10 suggested tags.
    """
    temp_path = os.path.join(UPLOAD_DIR, f"temp_{file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        tags = suggest_tags(temp_path, top_k=10)
    except Exception:
        os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tag suggestion failed"
        )

    os.remove(temp_path)
    return TagSuggestion(suggestions=tags)

@router.post("/photos/", response_model=PhotoOut)
async def create_photo(
    photo_in: PhotoCreate,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_photographer)
):
    """
    Final photo creation with selected tags.
    Saves file locally, creates DB record and tags.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    photo = crud.create_photo(
        db,
        user_id=current_user.id,
        filename=file.filename,
        caption=photo_in.caption
    )
    crud.add_photo_tags(db, photo.id, photo_in.selected_tags)
    return PhotoOut.from_orm(photo)

@router.get("/photos/{photo_id}/download")
async def download_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Download a photo file and increment its download count.
    """
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    file_path = os.path.join(UPLOAD_DIR, photo.filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    crud.increment_download_count(db, photo)
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=photo.filename
    )

@router.get("/photos/feed", response_model=PhotoList)
async def get_feed(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get paginated feed of photos from photographers the user follows.
    """
    follow_entries = crud.get_followees(db, current_user.id)
    # follow_entries might be list of tuples or objects
    followee_ids = [f.followee_id if hasattr(f, 'followee_id') else f[0] for f in follow_entries]
    photos = []
    if followee_ids:
        photos = (
            db.query(PhotoModel)
            .filter(PhotoModel.user_id.in_(followee_ids))
            .order_by(PhotoModel.upload_time.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    return PhotoList(items=photos, skip=skip, limit=limit)
