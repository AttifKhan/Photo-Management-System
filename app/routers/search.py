# Search by tags routes
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.engine import get_db
from app.db.crud import search_photos_by_sentence
from app.schemas.search import SearchResult
from app.schemas.photo import PhotoOut
from app.routers.dependencies import get_current_user

router = APIRouter(tags=["Search"])

import re
from inflect import engine as inflect_engine
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.db import crud, models 
from app.db.engine import get_db
from app.routers.dependencies import get_current_user

p = inflect_engine()

def extract_keywords(sentence: str) -> List[str]:
    # split on non-word chars, lowercase, drop empties
    words = re.split(r'\W+', sentence.lower())
    words = [w for w in words if w]
    # singularize simple plurals (e.g. "cats"→"cat")
    return list({ p.singular_noun(w) or w for w in words })

def search_photos_by_sentence(db: Session, sentence: str,
                              skip: int = 0, limit: int = 20):
    keys = extract_keywords(sentence)
    if not keys:
        return []

    # build a case-insensitive LIKE filter for each keyword
    filters = [
        func.lower(models.PhotoTag.tag_text).like(f"%{kw}%")
        for kw in keys
    ]

    # join Photo → PhotoTag, OR together, distinct, paginate
    return (
        db.query(models.Photo)
          .join(models.PhotoTag)
          .filter(or_(*filters))
          .distinct()
          .offset(skip)
          .limit(limit)
          .all()
    )

# @router.get("/search", response_model=SearchResult)
# async def search_photos(
#     query: str = Query(..., min_length=1, description="Search term for tags"),
#     skip: int = Query(0, ge=0),
#     limit: int = Query(20, ge=1),
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_user)
# ):
#     """
#     Search photos by tag text (case-insensitive, partial match).
#     Returns paginated list of matching photos.
#     """

#     photos = crud.search_photos_by_tag(db, query, skip=skip, limit=limit)
#     # Serialize via PhotoOut
#     items: List[PhotoOut] = [PhotoOut.from_orm(photo) for photo in photos]
#     return SearchResult(items=items, skip=skip, limit=limit)

@router.get("/search", response_model=SearchResult)
async def search_photos(
    query: str = Query(..., min_length=1, description="Search term or sentence for tags"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search photos by matching any keyword in the input sentence against tags.
    Supports simple plural → singular normalization.
    """
    photos = search_photos_by_sentence(db, query, skip=skip, limit=limit)
    items: List[PhotoOut] = [PhotoOut.from_orm(photo) for photo in photos]
    return SearchResult(items=items, skip=skip, limit=limit)