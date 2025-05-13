# Best photo of the day route
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.db.engine import get_db
from app.db import crud
from app.schemas.best_photo import BestPhotoOut
from app.schemas.photo import PhotoOut
from app.routers.dependencies import get_current_user

router = APIRouter(tags=["Best_photo"])

@router.get("/best-photo-today", response_model=BestPhotoOut)
async def best_photo_today(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the globally best photo of the current day.
    """
    target_date = date.today()
    # Ensure calculation is up-to-date
    record = crud.get_best_photo_of_day(db, target_date)
    if not record:
        record = crud.calculate_and_store_best_photo(db, target_date)
        if not record:
            raise HTTPException(status_code=404, detail="No photos available for today")
    
    # Now we can use BestPhotoOut's from_orm directly since it's fixed to use PhotoOut.from_orm
    return BestPhotoOut.from_orm(record)