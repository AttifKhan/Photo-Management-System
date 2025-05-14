# tests/test_photo.py
import os
import pytest
from unittest import mock
from io import BytesIO
from app.db.models import Photo, User, PhotoTag, Follow

class TestPhotoRoutes:
    def test_upload_photo_for_suggestions(self, client, photographer_token, mock_suggest_tags, mock_suggest_captions):
        """Test uploading a photo for tag and caption suggestions"""
        # Create a mock image file
        mock_image = BytesIO(b"fake image content")
        mock_image.name = "test_image.jpg"
        
        # Create headers with the token
        photographer_headers = {"Authorization": f"Bearer {photographer_token}"}
        
        # Configure mock returns
        mock_suggest_tags.return_value = ["tag1", "tag2", "tag3"]
        mock_suggest_captions.return_value = "Caption 1"
        
        response = client.post(
            "/photos/upload",
            files={"file": ("test_image.jpg", mock_image, "image/jpeg")},
            headers=photographer_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "captions" in data
        assert "suggestions" in data
        assert isinstance(data["captions"], str)
        assert len(data["suggestions"]) == 3
    
    def test_upload_photo_non_image(self, client, photographer_token):
        """Test that uploading a non-image file fails"""
        mock_file = BytesIO(b"not an image")
        mock_file.name = "not_image.txt"
        
        # Create headers with the token
        photographer_headers = {"Authorization": f"Bearer {photographer_token}"}
        
        response = client.post(
            "/photos/upload",
            files={"file": ("not_image.txt", mock_file, "text/plain")},
            headers=photographer_headers
        )
        
        assert response.status_code == 400
        assert "File must be an image" in response.json()["detail"]
    
    @mock.patch("os.path.join", return_value="/mock/path/test_image.jpg")
    @mock.patch("app.routers.photo.UPLOAD_DIR", "/mock/path")
    @mock.patch("os.makedirs")
    @mock.patch("os.access", return_value=True)
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("shutil.copyfileobj")
    def test_create_photo(self, mock_copyfileobj, mock_open, mock_exists, mock_access, 
                        mock_makedirs, mock_path_join, client, db, photographer_token):
        """Test creating a new photo with caption and tags"""
        # Set up the mock image file
        mock_image = BytesIO(b"fake image content")
        mock_image.name = "test_image.jpg"
        
        # Create headers with the token
        photographer_headers = {"Authorization": f"Bearer {photographer_token}"}
        
        # Create the photo
        response = client.post(
            "/photos/",
            files={"file": ("test_image.jpg", mock_image, "image/jpeg")},
            data={
                "caption": "Test photo caption",
                "tags": "tag1, tag2, tag3"
            },
            headers=photographer_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["caption"] == "Test photo caption"
        assert data["user_id"] == 2  # Test photographer ID
        
        # Verify photo exists in DB
        photo = db.query(Photo).filter(Photo.id == data["id"]).first()
        assert photo is not None
        assert photo.caption == "Test photo caption"
        
        # Verify tags were saved
        tags = db.query(PhotoTag).filter(PhotoTag.photo_id == photo.id).all()
        assert len(tags) == 3
        tag_texts = {tag.tag_text for tag in tags}
        assert tag_texts == {"tag1", "tag2", "tag3"}
    
    @mock.patch("fastapi.responses.FileResponse")
    @mock.patch("os.path.join", return_value="/mock/path/test_image.jpg")
    @mock.patch("app.routers.photo.UPLOAD_DIR", "/mock/path")
    @mock.patch("os.path.isfile", return_value=True)
    def test_download_photo(self, mock_isfile, mock_upload_dir, mock_path_join, 
                          mock_file_response, client, db, user_token):
        """Test downloading a photo increments the download count"""
        # Create headers with the token
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Create a photo in the DB
        photo = Photo(
            user_id=2,  # Test photographer ID
            filename="test_image.jpg",
            caption="Test photo",
            download_count=0
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)
        
        # Mock FileResponse to avoid actual file access
        mock_file_response.return_value = {"content": "mocked_file_content"}
        
        response = client.get(f"/photos/{photo.id}/download", headers=user_headers)
        
        # Verify download was successful
        mock_file_response.assert_called_once()
        
        # Verify download count was incremented
        db.refresh(photo)
        assert photo.download_count == 1
    
    def test_get_feed(self, client, db, user_token):
        """Test getting the photo feed shows photos from followed photographers"""
        # Create headers with the token
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Clear any existing photos to ensure clean test
        db.query(Photo).delete()
        db.commit()
        
        # Create a photo
        photo = Photo(
            user_id=2,  # Test photographer ID
            filename="test_photo.jpg",
            caption="Test photo"
        )
        db.add(photo)
        
        # Create a follow relationship
        follow = Follow(
            follower_id=1,  # Test user ID
            followee_id=2   # Test photographer ID
        )
        db.add(follow)
        db.commit()
        
        response = client.get("/photos/feed", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == photo.id
        assert data["items"][0]["caption"] == photo.caption
    
    def test_get_feed_no_follows(self, client, user_token):
        """Test that feed is empty when user follows no photographers"""
        # Create headers with the token
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        response = client.get("/photos/feed", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 0
    
    @mock.patch("app.routers.photo.request")
    def test_get_share_link_own_photo(self, mock_request, client, db, photographer_token):
        """Test getting share link for own photo"""
        # Create headers with the token
        photographer_headers = {"Authorization": f"Bearer {photographer_token}"}
        
        # Create a photo owned by the photographer
        photo = Photo(
            user_id=2,  # Test photographer ID
            filename="test_photo.jpg",
            caption="Test photo"
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)
        
        # Mock the URL construction
        mock_url_obj = mock.MagicMock()
        mock_url_obj.__str__.return_value = "http://testserver/static/uploads/test_photo.jpg"
        mock_request.url_for.return_value = mock_url_obj
        
        response = client.get(f"/photos/{photo.id}/share-link", headers=photographer_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "share_url" in data
        assert data["share_url"] == "http://testserver/static/uploads/test_photo.jpg"
    
    @mock.patch("app.routers.photo")
    def test_get_share_link_followed_photo(self, mock_request, client, db, user_token):
        """Test getting share link for a photo from a followed photographer"""
        # Create headers with the token
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Create a photo
        photo = Photo(
            user_id=2,  # Test photographer ID
            filename="test_photo.jpg",
            caption="Test photo"
        )
        db.add(photo)
        
        # Create a follow relationship
        follow = Follow(
            follower_id=1,  # Test user ID
            followee_id=2   # Test photographer ID
        )
        db.add(follow)
        db.commit()
        
        # Mock the URL construction
        mock_url_obj = mock.MagicMock()
        mock_url_obj.__str__.return_value = "http://testserver/static/uploads/test_photo.jpg"
        mock_request.url_for.return_value = mock_url_obj
        
        response = client.get(f"/photos/{photo.id}/share-link", headers=user_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "share_url" in data
    
    def test_get_share_link_not_following(self, client, db, user_token):
        """Test that getting share link fails if user doesn't follow the photographer"""
        # Create headers with the token
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Create photo but don't create follow relationship
        photo = Photo(
            user_id=2,  # Test photographer ID
            filename="test_photo.jpg",
            caption="Test photo"
        )
        db.add(photo)
        db.commit()
        
        response = client.get(f"/photos/{photo.id}/share-link", headers=user_headers)
        assert response.status_code == 403
        assert "You can only share photos from photographers you follow" in response.json()["detail"]

# Fixtures needed for tests
@pytest.fixture
def mock_suggest_tags():
    """Mock the suggest_tags function"""
    with mock.patch("app.ai.predictor.tags") as mock_func:
        yield mock_func
        
@pytest.fixture
def mock_suggest_captions():
    """Mock the suggest_captions function"""
    with mock.patch("app.ai.predictor.captions") as mock_func:
        yield mock_func

@pytest.fixture
def mock_file_response():
    """Mock the FileResponse class"""
    with mock.patch("fastapi.responses.FileResponse") as mock_func:
        yield mock_func