# Search by tags routes
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.engine import get_db
from app.db import crud
from app.schemas.search import SearchResult
from app.schemas.photo import PhotoOut
from app.routers.dependencies import get_current_user

router = APIRouter(tags=["search"])

@router.get("/search", response_model=SearchResult)
async def search_photos(
    query: str = Query(..., min_length=1, description="Search term for tags"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Search photos by tag text (case-insensitive, partial match).
    Returns paginated list of matching photos.
    """
    photos = crud.search_photos_by_tag(db, query, skip=skip, limit=limit)
    # Serialize via PhotoOut
    items: List[PhotoOut] = [PhotoOut.from_orm(photo) for photo in photos]
    return SearchResult(items=items, skip=skip, limit=limit)
