import os
import shutil
import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload

from app.db.engine import get_db
from app.db import crud
from app.db.models import Photo as PhotoModel
from app.schemas.photo import PhotoCreate, PhotoOut, TagSuggestion, PhotoList, ShareLinkOut
from app.routers.dependencies import get_current_user, require_photographer
from app.ai.predictor import suggest_tags, suggest_captions

router = APIRouter(tags=["Photo"])

# Directory to store uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "app/static/uploads")
# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/photos/upload", response_model=TagSuggestion)
async def upload_photo_with_caption_and_tags(
    file: UploadFile = File(...),
    current_user=Depends(require_photographer)
):
    """
    Uploads a photo temporarily, returns an AI-generated caption and top 10 tag suggestions.
    """
    # Save the uploaded file to a temporary location
    temp_path = os.path.join(UPLOAD_DIR, f"temp_{file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Generate caption and tags
        caption = suggest_captions(temp_path)
        tags = suggest_tags(temp_path, top_k=10)
    except Exception:
        # Clean up and report error
        os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Caption or tag suggestion failed"
        )

    # Remove temp file
    os.remove(temp_path)

    # Return combined response
    return TagSuggestion(caption=caption, suggestions=tags)

@router.post("/photos", response_model=PhotoOut)
async def create_photo(
    file: UploadFile = File(...),
    caption: str = Form(""),
    selected_tags: str = Form(""),
    db: Session = Depends(get_db),
    current_user = Depends(require_photographer)
):
    """
    Final photo creation with selected tags.
    Saves file locally, creates DB record and tags.
    """
    # Handle tags that might be comma-separated or JSON
    try:
        # First try to parse as JSON
        tags_list = json.loads(selected_tags)
    except json.JSONDecodeError:
        # If that fails, treat as comma-separated string
        tags_list = [tag.strip() for tag in selected_tags.split(',') if tag.strip()]
    
    # Create the photo file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Create the photo record
        photo = crud.create_photo(
            db,
            user_id=current_user.id,
            filename=file.filename,
            caption=caption
        )
        
        # Add the tags
        if tags_list:
            crud.add_photo_tags(db, photo.id, tags_list)
            
        return PhotoOut.from_orm(photo)
    except Exception as e:
        # If anything fails during DB operations, clean up the file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create photo: {str(e)}"
        )

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


from sqlalchemy.orm import joinedload
from app.db.models import Photo, User, Comment, Rating, PhotoTag

@router.get("/photos/feed", response_model=PhotoList)
async def get_feed(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get paginated feed of photos from photographers the user follows,
    including ratings, comments, and tags.
    """
    follow_entries = crud.get_followees(db, current_user.id)
    followee_ids = [f.followee_id if hasattr(f, 'followee_id') else f[0] for f in follow_entries]
    photos = []
    
    if followee_ids:
        # Query with eager loading for efficiency
        photo_models = (
            db.query(Photo)
            .filter(Photo.user_id.in_(followee_ids))
            .options(
                joinedload(Photo.owner),        # Load photographer data
                joinedload(Photo.tags),         # Load tags
                joinedload(Photo.ratings),      # Load ratings
                joinedload(Photo.comments)      # Load comments
                .joinedload(Comment.user)       # Load commenter data
            )
            .order_by(Photo.upload_time.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Convert to Pydantic models
        photos = [PhotoOut.from_orm(photo) for photo in photo_models]
    
    return PhotoList(items=photos, skip=skip, limit=limit)

# Share: Return JSON link
@router.get("/{photo_id}/share-link", response_model=ShareLinkOut)
def get_share_link(
    photo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # Changed from get_current_active_user to get_current_user
):
    # Get the photo
    photo = crud.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Check if the user has permission to share this photo
    # Case 1: It's the user's own photo
    if photo.user_id == current_user.id:
        pass  # User can share their own photos
    # Case 2: User follows the photographer who owns this photo
    elif not crud.is_following(db, follower_id=current_user.id, followed_id=photo.user_id):
        raise HTTPException(
            status_code=403, 
            detail="You can only share photos from photographers you follow"
        )
    
    # Convert the URL object to a string
    url_obj = request.url_for("static", path=f"uploads/{photo.filename}")
    share_url = str(url_obj)
    
    return ShareLinkOut(share_url=share_url)

# # Share: Return basic HTML page
# @router.get("/{photo_id}/share", response_class=HTMLResponse)
# def share_photo_page(
#     photo_id: int,
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     photo = crud.get_photo(db, photo_id)
#     if not photo:
#         raise HTTPException(status_code=404, detail="Photo not found")

#     image_url = request.url_for("static", path=f"uploads/{photo.filename}")
#     tags = ", ".join([t.tag_text for t in photo.tags])

#     html = f"""
#     <html>
#       <head><title>Shared Photo</title></head>
#       <body>
#         <h1>{photo.caption or 'Photo'}</h1>
#         <img src=\"{image_url}\" alt=\"photo\" style=\"max-width:90%;\" />
#         <p><strong>Tags:</strong> {tags}</p>
#         <p><em>Uploaded at {photo.upload_time}</em></p>
#       </body>
#     </html>
#     """
#     return HTMLResponse(content=html)