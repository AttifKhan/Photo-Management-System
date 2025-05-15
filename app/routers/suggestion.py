"""
Module for the suggestion router - provides recommendations for photographers to follow
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc, not_
from sqlalchemy.orm import Session

from app.db import models, crud
from app.db.engine import get_db
from app.routers.dependencies import get_current_user
from app.schemas.user import UserOut

router = APIRouter(tags=['Suggestions'])

@router.get("/suggestions", response_model=List[UserOut])
def get_photographer_suggestions(
    limit: int = Query(5, ge=1, le=20, description="Number of suggestions to return"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get suggested photographers to follow.

    This endpoint returns photographers that the user might be interested in following.
    The suggestions are based on:
    1. Popular photographers (most followers)
    2. Photographers followed by people the user follows
    3. Photographers who recently uploaded high-quality content

    The results exclude photographers the user already follows.
    """
    
    already_following = db.query(crud.Follow.followee_id).filter(
        crud.Follow.follower_id == current_user.id
    ).subquery()

    # Base query for photographers the user isn't already following
    base_query = db.query(models.User).filter(
        models.User.is_photographer == True,
        models.User.id != current_user.id,
        not_(models.User.id.in_(already_following))
    )

    # Strategy 1: Get popular photographers (most followers)
    popular_photographers = base_query.join(
        crud.Follow, crud.Follow.followee_id == models.User.id
    ).group_by(
        models.User.id
    ).order_by(
        desc(func.count(crud.Follow.id))
    ).limit(limit*2).all()


    # Strategy 2: Photographers followed by people the user follows
    followees = db.query(crud.Follow.followee_id).filter(
        crud.Follow.follower_id == current_user.id
    ).subquery()

    followee_follows = base_query.join(
        crud.Follow, crud.Follow.followee_id == models.User.id
    ).filter(
        crud.Follow.follower_id.in_(followees)
    ).group_by(
        models.User.id
    ).order_by(
        desc(func.count(crud.Follow.id))
    ).limit(limit*2).all()

    # Strategy 3: Recently active photographers with quality content
    recent_photographers = []
    if hasattr(models, 'Photo'):
        try:
            recent_photographers = base_query.join(
                models.Photo, models.Photo.user_id == models.User.id
            ).filter(
                models.Photo.download_count > 10  
            ).group_by(
                models.User.id
            ).order_by(
                desc(func.max(models.Photo.created_at))
            ).limit(limit*2).all()
        except (AttributeError, TypeError):
            recent_photographers = base_query.join(
                models.Photo, models.Photo.user_id == models.User.id
            ).group_by(
                models.User.id
            ).order_by(
                desc(func.max(models.Photo.created_at))
            ).limit(limit*2).all()

    # Get a list of unique suggestions
    unique_suggestions = {}
    
    # Add each photographer to our unique set, with a score based on their position
    # in each suggestion list
    for i, photographer in enumerate(popular_photographers):
        unique_suggestions[photographer.id] = {
            "user": photographer,
            "score": len(popular_photographers) - i
        }
    
    for i, photographer in enumerate(followee_follows):
        if photographer.id in unique_suggestions:
            unique_suggestions[photographer.id]["score"] += len(followee_follows) - i
        else:
            unique_suggestions[photographer.id] = {
                "user": photographer,
                "score": len(followee_follows) - i
            }
    
    for i, photographer in enumerate(recent_photographers):
        if photographer.id in unique_suggestions:
            unique_suggestions[photographer.id]["score"] += len(recent_photographers) - i
        else:
            unique_suggestions[photographer.id] = {
                "user": photographer,
                "score": len(recent_photographers) - i
            }
    
    # If we have too few suggestions, add some random photographers
    if len(unique_suggestions) < limit:
        random_photographers = base_query.filter(
            not_(models.User.id.in_([p_id for p_id in unique_suggestions.keys()]))
        ).order_by(
            func.random()
        ).limit(limit - len(unique_suggestions)).all()
        
        for photographer in random_photographers:
            unique_suggestions[photographer.id] = {
                "user": photographer,
                "score": 0  # Lowest score for random suggestions
            }
    
    # Sort by score and get the top 'limit' suggestions
    sorted_suggestions = sorted(
        unique_suggestions.values(), 
        key=lambda x: x["score"], 
        reverse=True
    )[:limit]
    
    return [UserOut.model_validate(item["user"]) for item in sorted_suggestions]