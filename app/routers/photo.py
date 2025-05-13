import os
import shutil
import json
import uuid
import imghdr
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from app.db.engine import get_db
from app.db import crud
from app.db.models import Photo as PhotoModel
from app.schemas.photo import PhotoCreate, PhotoOut, TagSuggestion, PhotoList, ShareLinkOut
from app.db.models import Photo, User, Comment, Rating, PhotoTag
from app.routers.dependencies import get_current_user, require_photographer
from app.ai.predictor import captions, tags

router = APIRouter(tags=["Photo"])

# Directory for temporary file uploads
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/tmp/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/photos/upload", response_model=TagSuggestion)
async def upload_photo(
    file: UploadFile = File(...),
    caption_count: int = 3,
    tag_count: int = 10, 
    current_user=Depends(require_photographer)
) -> TagSuggestion:
    """
    Upload a photo and get AI-generated caption and tag suggestions.
    
    Args:
        file: Image file upload
        caption_count: Number of captions to generate
        tag_count: Number of tags to generate
        current_user: Authenticated photographer user
        
    Returns:
        TagSuggestion object with lists of captions and tag suggestions
    """
    # Validate file type
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")
    
    # Save temporarily
    filename = f"{uuid.uuid4()}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # Save the uploaded file
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Verify it's actually an image
        if not imghdr.what(path):
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Generate captions and tags using our utility functions
        caption_list = captions(path, count=caption_count)
        tag_list = tags(path, count=tag_count)
        
        return TagSuggestion(
            captions=caption_list,
            suggestions=tag_list
        )
    except Exception as e:
        # Log the error (in a real app)
        print(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing image")
    finally:
        # Clean up the temporary file
        try:
            os.remove(path)
        except OSError:
            pass



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure this matches your project structure
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')



def parse_tags(tags_str: Optional[str]) -> List[str]:
    """
    Parse comma-separated tags string into a list of tags.
    
    Args:
        tags_str (Optional[str]): Comma-separated string of tags
    
    Returns:
        List[str]: List of cleaned, unique tags
    """
    if not tags_str:
        return []
    
    # Split by comma, strip whitespace, remove empty strings, convert to lowercase
    tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(tags))

def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename while preserving the original extension.
    
    Args:
        original_filename (str): The original filename of the uploaded file
    
    Returns:
        str: A unique filename
    """
    # Split the original filename into name and extension
    name, ext = os.path.splitext(original_filename)
    
    # Generate a unique identifier
    unique_id = uuid.uuid4().hex[:8]  # Use first 8 characters of UUID
    
    # Sanitize the original filename (remove any non-alphanumeric characters except underscores and hyphens)
    sanitized_name = ''.join(
        char for char in name 
        if char.isalnum() or char in ('-', '_')
    )
    
    # Truncate the sanitized name if it's too long
    max_name_length = 50
    sanitized_name = sanitized_name[:max_name_length]
    
    # Combine sanitized name, unique ID, and extension
    unique_filename = f"{sanitized_name}_{unique_id}{ext}"
    
    return unique_filename

@router.post("/photos/", response_model=PhotoOut)
async def create_photo(
    caption: Optional[str] = Form(None),  # Optional caption
    tags: Optional[str] = Form(None),  # Comma-separated tags string
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_photographer)
):
    """
    Create a new photo with optional caption and tags.
    Saves file locally and creates DB record.
    
    Tags should be comma-separated, e.g., "quote, inspirational, black, text, motivation"
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Invalid file")

        # Log current upload directory and ensure it exists
        logger.info(f"Upload directory: {UPLOAD_DIR}")
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Verify directory is writable
        if not os.access(UPLOAD_DIR, os.W_OK):
            logger.error(f"Upload directory is not writable: {UPLOAD_DIR}")
            raise HTTPException(status_code=500, detail="Server configuration error: Upload directory not writable")

        # Generate a unique filename while preserving original name and extension
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save the file
        try:
            with open(file_path, "wb") as buffer:
                # Use copyfileobj for efficient file copying
                shutil.copyfileobj(file.file, buffer)
            
            # Verify file was saved
            if not os.path.exists(file_path):
                raise HTTPException(status_code=500, detail="Failed to save uploaded file")
            
        except PermissionError:
            raise HTTPException(status_code=500, detail="Permission denied when saving file")
        except Exception as save_error:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(save_error)}")

        # Parse tags
        selected_tags = parse_tags(tags)

        # Create photo record
        photo = crud.create_photo(
            db,
            user_id=current_user.id,
            filename=unique_filename,  # Use the unique filename
            caption=caption
        )
        
        # Add tags to the photo if any
        if selected_tags:
            crud.add_photo_tags(db, photo.id, selected_tags)
        print(PhotoOut.from_orm(photo))
        # Return the photo using the from_orm class method
        return PhotoOut.from_orm(photo)
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error processing photo upload: {str(e)}")

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

