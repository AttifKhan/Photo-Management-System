# Photographer suggestion route
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.db.engine import get_db
from app.db.models import Follow, User as UserModel
from app.schemas.suggestion import SuggestionOut
from app.routers.dependencies import get_current_user

router = APIRouter(tags=["suggestion"])

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
