# ORM model definitions
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.engine import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_photographer = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    photos = relationship("Photo", back_populates="owner", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    follows = relationship(
        "Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan"
    )
    followers = relationship(
        "Follow", foreign_keys="Follow.followee_id", back_populates="followee", cascade="all, delete-orphan"
    )


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    caption = Column(Text)
    upload_time = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    upload_date = Column(Date, default=date.today, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)

    owner = relationship("User", back_populates="photos")
    comments = relationship("Comment", back_populates="photo", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="photo", cascade="all, delete-orphan")
    tags = relationship("PhotoTag", back_populates="photo", cascade="all, delete-orphan")
    best_photo = relationship("BestPhotoOfTheDay", back_populates="photo", cascade="all, delete-orphan")


class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    followee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    follower = relationship(
        "User", foreign_keys=[follower_id], back_populates="follows"
    )
    followee = relationship(
        "User", foreign_keys=[followee_id], back_populates="followers"
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    photo = relationship("Photo", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    photo = relationship("Photo", back_populates="ratings")
    user = relationship("User", back_populates="ratings")


class PhotoTag(Base):
    __tablename__ = "photo_tags"

    id = Column(Integer, primary_key=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    tag_text = Column(String(100), index=True, nullable=False)

    photo = relationship("Photo", back_populates="tags")



class BestPhotoOfTheDay(Base):
    __tablename__ = "best_photo_of_the_day"

    date = Column(Date, primary_key=True, default=date.today)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    selected_at = Column(DateTime, default=datetime.now(timezone.utc))

    photo = relationship("Photo", back_populates="best_photo")