# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import StaticPool

# from app.main import app
# from app.db.engine import Base, get_db
# from app.core.security import create_access_token, hash_password
# from app.db.models import User, Photo, Comment, Rating, Follow, PhotoTag, Tag, BestPhotoOfTheDay
# from datetime import datetime, timedelta, date
# import os
# import shutil
# import jwt # type: ignore
from typing import Generator, Dict, Any

import sys
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now we can import from app
from app.main import app
from app.db.engine import get_db
from app.db.models import Base
from app.db.models import User as UserModel
from app.routers.dependencies import get_current_user
from app.db.models import User, Photo, Comment, Rating, Follow, PhotoTag, BestPhotoOfTheDay
from app.core.security import create_access_token, hash_password

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import os
from typing import Generator, Any, Dict
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


pytest_plugins = ['pytest_asyncio']

asyncio_mode = "strict"

def pytest_configure(config):
    config.option.asyncio_mode = "auto"
    

# Use in-memory SQLite for testing
TEST_SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "mysql+pymysql://root:Code%407338677189@localhost/test_photoshare")

# Create test engine
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test user fixtures
TEST_USER = {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
    "is_photographer": False,
    "is_admin": False
}

TEST_PHOTOGRAPHER = {
    "id": 2,
    "username": "testphotographer",
    "email": "photographer@example.com",
    "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
    "is_photographer": True,
    "is_admin": False
}

TEST_ADMIN = {
    "id": 3,
    "username": "testadmin",
    "email": "admin@example.com",
    "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
    "is_photographer": False,
    "is_admin": True
}

TEST_PHOTO = {
    "id": 1,
    "user_id": 2,  # photographer
    "filename": "test_photo.jpg",
    "caption": "Test Caption",
    "upload_time": datetime.now(),
    "download_count": 0
}

# Override the get_db dependency
@pytest.fixture
def db() -> Generator:
    """
    Fixture to provide a test database session
    """
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create a test session
        db = TestingSessionLocal()
        
        # Setup test users
        test_user = User(**TEST_USER)
        test_photographer = User(**TEST_PHOTOGRAPHER)
        test_admin = User(**TEST_ADMIN)
        
        for user in [test_user, test_photographer, test_admin]:
            db_user = db.query(User).filter(User.id == user.id).first()
            if not db_user:
                db.add(user)
        
        # Add a test photo
        test_photo = Photo(**TEST_PHOTO)
        db_photo = db.query(Photo).filter(Photo.id == test_photo.id).first()
        if not db_photo:
            db.add(test_photo)
            
        db.commit()
        
        yield db
    finally:
        db.close()
        # Drop all tables after tests
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db) -> Generator:
    """
    Fixture to create a test client with overridden dependencies
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    
    # Reset dependency overrides after test
    app.dependency_overrides = {}

@pytest.fixture
def user_token() -> str:
    """Generate JWT token for normal user"""
    access_token = create_access_token(
        data={"sub": str(TEST_USER["id"])},
        expires_delta=timedelta(minutes=30)
    )
    return access_token

@pytest.fixture
def photographer_token() -> str:
    """Generate JWT token for photographer user"""
    access_token = create_access_token(
        data={"sub": str(TEST_PHOTOGRAPHER["id"])},
        expires_delta=timedelta(minutes=30)
    )
    return access_token

@pytest.fixture
def admin_token() -> str:
    """Generate JWT token for admin user"""
    access_token = create_access_token(
        data={"sub": str(TEST_ADMIN["id"])},
        expires_delta=timedelta(minutes=30)
    )
    return access_token

@pytest.fixture
def mock_current_user() -> MagicMock:
    """Mock the current user dependency"""
    mock_user = MagicMock()
    mock_user.id = TEST_USER["id"]
    mock_user.is_photographer = TEST_USER["is_photographer"]
    mock_user.is_admin = TEST_USER["is_admin"]
    return mock_user

@pytest.fixture
def mock_photographer_user() -> MagicMock:
    """Mock the current photographer user dependency"""
    mock_user = MagicMock()
    mock_user.id = TEST_PHOTOGRAPHER["id"]
    mock_user.is_photographer = TEST_PHOTOGRAPHER["is_photographer"]
    mock_user.is_admin = TEST_PHOTOGRAPHER["is_admin"]
    return mock_user

@pytest.fixture
def mock_admin_user() -> MagicMock:
    """Mock the current admin user dependency"""
    mock_user = MagicMock()
    mock_user.id = TEST_ADMIN["id"]
    mock_user.is_photographer = TEST_ADMIN["is_photographer"]
    mock_user.is_admin = TEST_ADMIN["is_admin"]
    return mock_user

@pytest.fixture
def mock_db() -> MagicMock:
    """Mock the database session"""
    return MagicMock()



# Create fixtures for test data and mocked responses
@pytest.fixture
def test_photo_data() -> Dict[str, Any]:
    return {
        "id": 1,
        "user_id": 2,
        "filename": "test.jpg",
        "caption": "Test photo",
        "upload_time": datetime.now().isoformat(),
        "download_count": 0
    }

@pytest.fixture
def test_comment_data() -> Dict[str, Any]:
    return {
        "id": 1,
        "user_id": 1,
        "photo_id": 1,
        "content": "This is a test comment",
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def test_rating_data() -> Dict[str, Any]:
    return {
        "id": 1,
        "user_id": 1,
        "photo_id": 1,
        "score": 4,
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def test_follow_data() -> Dict[str, Any]:
    return {
        "id": 1,
        "follower_id": 1,
        "followee_id": 2,
        "created_at": datetime.now().isoformat()
    }

# Mock file upload
@pytest.fixture
def mock_upload_file(monkeypatch):
    """Mock UploadFile for testing file uploads"""
    class MockUpload:
        def __init__(self, filename="test.jpg"):
            self.filename = filename
            self.file = MagicMock()
            self.file.read = MagicMock(return_value=b"test file content")
    
    return MockUpload()

# Mock the AI suggestion services
@pytest.fixture
def mock_suggest_tags(monkeypatch):
    """Mock the suggest_tags function in the AI module"""
    def mock_suggest(*args, **kwargs):
        return ["nature", "landscape", "mountain", "sky", "clouds"]
    
    monkeypatch.setattr("app.ai.predictor.suggest_tags", mock_suggest)
    return mock_suggest

@pytest.fixture
def mock_suggest_captions(monkeypatch):
    """Mock the suggest_captions function in the AI module"""
    def mock_suggest(*args, **kwargs):
        return "A beautiful mountain landscape under cloudy skies"
    
    monkeypatch.setattr("app.ai.predictor.suggest_captions", mock_suggest)
    return mock_suggest

# Mock file operations
@pytest.fixture
def mock_file_ops(monkeypatch):
    """Mock file operations for testing"""
    # Mock open function
    mock_open = MagicMock()
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Mock shutil.copyfileobj
    mock_copy = MagicMock()
    monkeypatch.setattr("shutil.copyfileobj", mock_copy)
    
    # Mock os.path.exists
    mock_exists = MagicMock(return_value=True)
    monkeypatch.setattr("os.path.exists", mock_exists)
    
    # Mock os.path.isfile
    mock_isfile = MagicMock(return_value=True)
    monkeypatch.setattr("os.path.isfile", mock_isfile)
    
    # Mock os.remove
    mock_remove = MagicMock()
    monkeypatch.setattr("os.remove", mock_remove)
    
    return {
        "open": mock_open, 
        "copy": mock_copy, 
        "exists": mock_exists,
        "isfile": mock_isfile, 
        "remove": mock_remove
    }