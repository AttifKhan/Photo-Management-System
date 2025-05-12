import os
import io
import uuid
import imghdr
import shutil
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from app.routers.photo import (
    router, parse_tags, generate_unique_filename, UPLOAD_DIR as ROUTER_UPLOAD_DIR
)
from app.db import crud
from app.schemas.photo import TagSuggestion, PhotoOut, PhotoList, ShareLinkOut

# Create FastAPI app for testing
app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture(autouse=True)
def tmp_upload_dir(tmp_path, monkeypatch):
    # Override the upload directory to a temporary path
    tmp_dir = tmp_path / "uploads"
    tmp_dir.mkdir()
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_dir))
    # Also override in router module
    monkeypatch.setattr("app.routers.photo.UPLOAD_DIR", str(tmp_dir))
    return tmp_dir

def test_parse_tags_empty():
    assert parse_tags(None) == []
    assert parse_tags("") == []

def test_parse_tags_basic():
    tags_str = "Tag1, tag2, TAG1 , , tag3"
    result = parse_tags(tags_str)
    assert result == ["tag1", "tag2", "tag3"]

def test_generate_unique_filename_preserves_extension_and_sanitizes():
    original = "My Photo!.jpg"
    unique = generate_unique_filename(original)
    name, ext = os.path.splitext(unique)
    assert ext == ".jpg"
    # sanitized name should only contain alphanumeric, _ or -
    base = name.rsplit("_", 1)[0]
    assert base.isalnum()
    # unique id length
    uid = name.rsplit("_", 1)[1]
    assert len(uid) == 8

class DummyUser:
    id = 1

class DummyPhotoModel:
    def __init__(self, id, filename, user_id):
        self.id = id
        self.filename = filename
        self.user_id = user_id

# Mock predictor functions
@pytest.fixture(autouse=True)
def mock_predictors(monkeypatch):
    monkeypatch.setattr("app.routers.photo.captions", lambda path, count: [f"Caption {i}" for i in range(count)])
    monkeypatch.setattr("app.routers.photo.tags", lambda path, count: [f"tag{i}" for i in range(count)])

# Mock authentication dependency for photographers
@pytest.fixture(autouse=True)
def mock_require_photographer(monkeypatch):
    monkeypatch.setattr("app.routers.photo.require_photographer", lambda: DummyUser())
    monkeypatch.setattr("app.routers.photo.get_current_user", lambda: DummyUser())
    return

# Mock DB crud functions
@pytest.fixture(autouse=True)
def mock_crud(monkeypatch):
    monkeypatch.setattr(crud, "create_photo", lambda db, user_id, filename, caption: DummyPhotoModel(42, filename, user_id))
    monkeypatch.setattr(crud, "add_photo_tags", lambda db, photo_id, tags: None)
    monkeypatch.setattr(crud, "get_photo", lambda db, pid: DummyPhotoModel(pid, "file.jpg", 1) if pid == 1 else None)
    monkeypatch.setattr(crud, "increment_download_count", lambda db, photo: None)
    monkeypatch.setattr(crud, "get_followees", lambda db, uid: [])
    monkeypatch.setattr(crud, "is_following", lambda db, follower_id, followed_id: True)

# Helper to create a minimal JPEG file
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00"*100 + b"\xff\xd9"

def test_upload_photo_success(tmp_upload_dir):
    file_content = JPEG_HEADER
    files = {"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
    response = client.post("/photos/upload?caption_count=2&tag_count=3", files=files)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == {"captions": ["Caption 0", "Caption 1"], "suggestions": ["tag0", "tag1", "tag2"]}

def test_upload_photo_invalid_type(tmp_upload_dir):
    files = {"file": ("test.txt", io.BytesIO(b"not image"), "text/plain")}
    response = client.post("/photos/upload", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_upload_photo_invalid_image(tmp_upload_dir):
    # image content but not valid image header
    files = {"file": ("test.jpg", io.BytesIO(b"randomdata"), "image/jpeg")}
    response = client.post("/photos/upload", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_create_photo_success(tmp_upload_dir):
    file_content = JPEG_HEADER
    files = {"file": ("orig.jpg", io.BytesIO(file_content), "image/jpeg")}
    data = {"caption": "A caption", "tags": "a, b, a"}
    response = client.post("/photos/", data=data, files=files)
    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["id"] == 42
    assert json_data["filename"].endswith(".jpg")
    assert json_data["caption"] == "A caption"

def test_download_photo_not_found(tmp_upload_dir):
    response = client.get("/photos/999/download")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_download_photo_success(tmp_upload_dir):
    # create dummy file in upload dir
    path = tmp_upload_dir / "file.jpg"
    with open(path, "wb") as f:
        f.write(b"data")
    response = client.get("/photos/1/download")
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b"data"
    assert response.headers["content-disposition"].startswith("attachment;")

def test_get_feed_empty(monkeypatch):
    response = client.get("/photos/feed")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []

from fastapi import Request

def test_get_share_link_own(monkeypatch):
    # simulate request.url_for
    class DummyRequest:
        def url_for(self, name, path):
            return f"http://testserver/static/{path}"
    response = client.get("/photos/1/share-link")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "share_url" in data

def test_get_share_link_forbidden(monkeypatch):
    # mock is_following to False
    monkeypatch.setattr(crud, "is_following", lambda db, follower_id, followed_id: False)
    response = client.get("/photos/2/share-link")
    assert response.status_code == status.HTTP_403_FORBIDDEN
