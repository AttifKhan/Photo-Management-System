# Photographer suggestion route
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, not_
from typing import List
from app.db.engine import get_db
from app.db import crud, models
from app.routers.dependencies import get_current_user
from app.schemas.follow import FollowOut
from app.schemas.user import UserOut
from app.db.models import Follow, User as UserModel
from app.schemas.suggestion import SuggestionOut
from app.routers.dependencies import get_current_user

router = APIRouter(tags=["Suggestion"])

@router.get("/suggestions", response_model=list[SuggestionOut])
def suggest_photographers(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    limit: int = 5
):
    """
    Suggest photographers to follow based on who your followees follow (collaborative filtering).
    """
    # First-level: users current_user follows
    first_level = db.query(Follow.followee_id).filter(Follow.follower_id == current_user.id).subquery()
    # Second-level: who those users follow, excluding already followed and self
    second_level = (
        db.query(
            Follow.followee_id.label('user_id'),
            func.count(Follow.follower_id).label('score')
        )
        .filter(Follow.follower_id.in_(first_level))
        .filter(Follow.followee_id != current_user.id)
        .filter(~Follow.followee_id.in_(first_level))
        .group_by(Follow.followee_id)
        .order_by(desc('score'))
        .limit(limit)
        .all()
    )
    user_ids = [row.user_id for row in second_level]
    users = db.query(UserModel).filter(UserModel.id.in_(user_ids)).all()
    # Map scores to users
    score_map = {row.user_id: row.score for row in second_level}
    return [SuggestionOut(id=u.id, username=u.username, score=score_map.get(u.id, 0)) for u in users]

  # Assuming you have this schema for user output



# Add this new endpoint for suggestions
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
    # Get IDs of photographers the user already follows
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
    
    # Strategy 4: Recently active photographers with quality content
    # Adjust based on how you determine "quality" in your app
    recent_photographers = []
    if hasattr(models, 'Photo'):
        recent_photographers = base_query.join(
            models.Photo, models.Photo.user_id == models.User.id
        ).filter(
            models.Photo.likes_count > 10  # Assuming you track likes
        ).group_by(
            models.User.id
        ).order_by(
            desc(func.max(models.Photo.created_at))
        ).limit(limit*2).all()
    
    # Combine results from different strategies, removing duplicates
    all_suggestions = []
    
    # Add photographers in order of strategy priority
    for photographer_list in [popular_photographers, followee_follows, recent_photographers]:
        for photographer in photographer_list:
            if photographer not in all_suggestions:
                all_suggestions.append(photographer)
                if len(all_suggestions) >= limit:
                    break
        if len(all_suggestions) >= limit:
            break
    
    # If we don't have enough suggestions, get random photographers as fallback
    if len(all_suggestions) < limit:
        remaining_count = limit - len(all_suggestions)
        existing_ids = [p.id for p in all_suggestions]
        
        random_photographers = base_query.filter(
            not_(models.User.id.in_(existing_ids))
        ).order_by(
            func.random()
        ).limit(remaining_count).all()
        
        all_suggestions.extend(random_photographers)
    
    # Convert to UserOut schema
    return [UserOut.model_validate(photographer) for photographer in all_suggestions[:limit]]