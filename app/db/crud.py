# CRUD operations
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import re
from inflect import engine as inflect_engine
from sqlalchemy import or_, func
from typing import List
from app.db.models import (
    User, Photo, Follow, Comment, Rating, PhotoTag, BestPhotoOfTheDay
)

# ----- User CRUD -----
def create_user(db: Session, username: str, email: str, hashed_password: str, is_photographer: bool = False, is_admin: bool = False):
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_photographer=is_photographer,
        is_admin=is_admin
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


# ----- Photo CRUD -----
def create_photo(db: Session, user_id: int, filename: str, caption: str = None):
    photo = Photo(
        user_id=user_id,
        filename=filename,
        caption=caption
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def get_photo(db: Session, photo_id: int):
    return db.query(Photo).filter(Photo.id == photo_id).first()


def get_photos_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Photo).filter(Photo.user_id == user_id).offset(skip).limit(limit).all()


def increment_download_count(db: Session, photo: Photo):
    photo.download_count += 1
    db.commit()
    db.refresh(photo)
    return photo


# ----- Follow CRUD -----
def follow_user(db: Session, follower_id: int, followee_id: int):
    follow = Follow(follower_id=follower_id, followee_id=followee_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return follow


def unfollow_user(db: Session, follower_id: int, followee_id: int):
    db.query(Follow).filter(
        Follow.follower_id == follower_id,
        Follow.followee_id == followee_id
    ).delete()
    db.commit()


def get_followees(db: Session, user_id: int):
    return db.query(Follow.followee_id).filter(Follow.follower_id == user_id).all()


# ----- Comment CRUD -----
def create_comment(db: Session, user_id: int, photo_id: int, content: str):
    comment = Comment(user_id=user_id, photo_id=photo_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments_by_photo(db: Session, photo_id: int):
    return db.query(Comment).filter(Comment.photo_id == photo_id).order_by(Comment.created_at.desc()).all()


# ----- Rating CRUD -----
def create_rating(db: Session, user_id: int, photo_id: int, score: int):
    rating = Rating(user_id=user_id, photo_id=photo_id, score=score)
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


def get_ratings_by_photo(db: Session, photo_id: int):
    return db.query(Rating).filter(Rating.photo_id == photo_id).all()


def get_average_rating(db: Session, photo_id: int):
    avg = db.query(func.avg(Rating.score)).filter(Rating.photo_id == photo_id).scalar()
    return float(avg) if avg is not None else 0.0


# ----- Tag CRUD -----
def add_photo_tags(db: Session, photo_id: int, tags: list[str]):
    objects = [PhotoTag(photo_id=photo_id, tag_text=tag) for tag in tags]
    db.add_all(objects)
    db.commit()
    return objects


def get_tags_by_photo(db: Session, photo_id: int):
    return db.query(PhotoTag).filter(PhotoTag.photo_id == photo_id).all()


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
        func.lower(PhotoTag.tag_text).like(f"%{kw}%")
        for kw in keys
    ]

    # join Photo → PhotoTag, OR together, distinct, paginate
    return (
        db.query(Photo)
          .join(PhotoTag)
          .filter(or_(*filters))
          .distinct()
          .offset(skip)
          .limit(limit)
          .all()
    )
def search_photos_by_tag(db: Session, query: str, skip: int = 0, limit: int = 100):
    return (
        db.query(Photo)
        .join(PhotoTag)
        .filter(PhotoTag.tag_text.like(f"%{query}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )


#Best Photo of the Day CRUD 
def set_best_photo_of_day(db: Session, target_date: date, photo_id: int):

    record = db.query(BestPhotoOfTheDay).filter(BestPhotoOfTheDay.date == target_date).first()
    if record:
        record.photo_id = photo_id
        record.selected_at = func.now()
    else:
        record = BestPhotoOfTheDay(date=target_date, photo_id=photo_id)
        db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_best_photo_of_day(db: Session, target_date: date):
    return db.query(BestPhotoOfTheDay).filter(BestPhotoOfTheDay.date == target_date).first()


def calculate_and_store_best_photo(db: Session, target_date: date = date.today()):
    photos = db.query(Photo).filter(Photo.upload_date == target_date).all()
    best = None
    best_score = -1
    for photo in photos:
        avg_rating = get_average_rating(db, photo.id)
        comment_count = db.query(func.count(Comment.id)).filter(Comment.photo_id == photo.id).scalar() or 0
        download_count = photo.download_count
        # Score formula
        score = (avg_rating * 2) + (comment_count * 0.5) + (download_count * 0.2)
        if score > best_score:
            best_score = score
            best = photo
    if best:
        return set_best_photo_of_day(db, target_date, best.id)
    return None



def get_follow(db: Session, follower_id: int, followee_id: int):
    """
    Check if a follow relationship exists between follower and followee.
    Returns the Follow object if it exists, None otherwise.
    """
    return db.query(Follow).filter(
        Follow.follower_id == follower_id,
        Follow.followee_id == followee_id
    ).first()


def check_follow_exists(db: Session, follower_id: int, followee_id: int) -> bool:
    """
    Check if a follow relationship exists between follower and followee.
    Returns True if it exists, False otherwise.
    """
    follow = get_follow(db, follower_id, followee_id)
    return follow is not None


def follow_user(db: Session, follower_id: int, followee_id: int):
    """
    Create a follow relationship between follower and followee.
    Returns the created Follow object.
    """
    follow = Follow(
        follower_id=follower_id,
        followee_id=followee_id
    )
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return follow


def get_followers(db: Session, user_id: int):
    """
    Get all users that are following the specified user.
    Returns a list of user IDs.
    """
    followers = db.query(Follow.follower_id).filter(Follow.followee_id == user_id).all()
    return followers

def is_following(db: Session, follower_id: int, followed_id: int) -> bool:
    """
    Check if a user follows another user
    
    Args:
        db: Database session
        follower_id: ID of the user who might be following
        followed_id: ID of the user who might be followed
    
    Returns:
        True if follower_id follows followed_id, False otherwise
    """

    follow_relationship = db.query(Follow).filter(
        Follow.follower_id == follower_id,
        Follow.followee_id == followed_id
    ).first()
    
    return follow_relationship is not None