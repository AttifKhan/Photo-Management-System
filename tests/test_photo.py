import pytest
import os
import json
from unittest.mock import patch, MagicMock, mock_open
from fastapi import UploadFile, HTTPException, status
from fastapi.responses import FileResponse

from app.routers.photo import (
    upload_photo_with_caption_and_tags,
    create_photo,
    download_photo,
    get_feed,
    get_share_link,
)

class TestPhotoRoutes:
    @patch("app.ai.predictor.suggest_captions")
    @patch("app.ai.predictor.suggest_tags")
    @patch("os.path.join")
    @patch("os.remove")
    async def test_upload_photo_for_suggestions(
        self, mock_remove, mock_join, mock_suggest_tags, mock_suggest_captions, 
        mock_upload_file, mock_photographer_user
    ):
        """Test uploading a photo for AI suggestions"""
        # Setup mocks
        mock_join.return_value = "/tmp/temp_test.jpg"
        mock_suggest_captions.return_value = "A beautiful sunset"
        mock_suggest_tags.return_value = ["sunset", "nature", "sky", "clouds", "orange"]
        
        # Mock open function
        m = mock_open()
        with patch("builtins.open", m):
            result = await upload_photo_with_caption_and_tags(
                file=mock_upload_file,
                current_user=mock_photographer_user
            )
        
        # Verify result
        assert result.caption == "A beautiful sunset"
        assert len(result.suggestions) == 5
        assert "sunset" in result.suggestions
        
        # Verify mocks were called correctly
        m.assert_called_once_with("/tmp/temp_test.jpg", "wb")
        mock_suggest_captions.assert_called_once_with("/tmp/temp_test.jpg")
        mock_suggest_tags.assert_called_once_with("/tmp/temp_test.jpg", top_k=10)
        mock_remove.assert_called_once_with("/tmp/temp_test.jpg")
    
    @patch("app.ai.predictor.suggest_captions")
    @patch("app.ai.predictor.suggest_tags")
    @patch("os.path.join")
    @patch("os.remove")
    async def test_upload_photo_suggestion_failure(
        self, mock_remove, mock_join, mock_suggest_tags, mock_suggest_captions, 
        mock_upload_file, mock_photographer_user
    ):
        """Test handling errors during AI suggestion"""
        # Setup mocks
        mock_join.return_value = "/tmp/temp_test.jpg"
        mock_suggest_captions.side_effect = Exception("AI service unavailable")
        
        # Mock open function
        m = mock_open()
        with patch("builtins.open", m):
            with pytest.raises(HTTPException) as exc_info:
                await upload_photo_with_caption_and_tags(
                    file=mock_upload_file,
                    current_user=mock_photographer_user
                )
        
        # Verify exception details
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Caption or tag suggestion failed"
        
        # Verify cleanup was performed
        mock_remove.assert_called_once_with("/tmp/temp_test.jpg")
    
    @patch("app.db.crud.create_photo")
    @patch("app.db.crud.add_photo_tags")
    @patch("os.path.join")
    @patch("builtins.open", new_callable=mock_open)
    async def test_create_photo_success(
        self, mock_file, mock_join, mock_add_tags, mock_create_photo,
        mock_upload_file, mock_db, mock_photographer_user
    ):
        """Test successfully creating a photo with tags"""
        # Setup mocks
        mock_join.return_value = "/app/static/uploads/test.jpg"
        
        mock_photo = MagicMock()
        mock_photo.id = 1
        mock_photo.user_id = mock_photographer_user.id
        mock_photo.filename = "test.jpg"
        mock_photo.caption = "Beautiful sunset"
        mock_create_photo.return_value = mock_photo
        
        # Call the function with JSON-formatted tags
        result = await create_photo(
            file=mock_upload_file,
            caption="Beautiful sunset",
            selected_tags=json.dumps(["sunset", "nature"]),
            db=mock_db,
            current_user=mock_photographer_user
        )
        
        # Verify result
        assert result.id == 1
        assert result.filename == "test.jpg"
        assert result.caption == "Beautiful sunset"
        
        # Verify mocks were called correctly
        mock_file.assert_called_once_with("/app/static/uploads/test.jpg", "wb")
        mock_create_photo.assert_called_once_with(
            mock_db,
            user_id=mock_photographer_user.id,
            filename="test.jpg",
            caption="Beautiful sunset"
        )
        mock_add_tags.assert_called_once_with(mock_db, 1, ["sunset", "nature"])
    
    @patch("app.db.crud.create_photo")
    @patch("app.db.crud.add_photo_tags")
    @patch("os.path.join")
    @patch("builtins.open", new_callable=mock_open)
    async def test_create_photo_with_comma_tags(
        self, mock_file, mock_join, mock_add_tags, mock_create_photo,
        mock_upload_file, mock_db, mock_photographer_user
    ):
        """Test creating a photo with comma-separated tags"""
        # Setup mocks
        mock_join.return_value = "/app/static/uploads/test.jpg"
        
        mock_photo = MagicMock()
        mock_photo.id = 1
        mock_photo.user_id = mock_photographer_user.id
        mock_photo.filename = "test.jpg"
        mock_photo.caption = "Beautiful sunset"
        mock_create_photo.return_value = mock_photo
        
        # Call the function with comma-separated tags
        result = await create_photo(
            file=mock_upload_file,
            caption="Beautiful sunset",
            selected_tags="sunset, nature",
            db=mock_db,
            current_user=mock_photographer_user
        )
        
        # Verify result
        assert result.id == 1
        assert result.filename == "test.jpg"
        assert result.caption == "Beautiful sunset"
        
        # Verify mocks were called correctly
        mock_add_tags.assert_called_once_with(mock_db, 1, ["sunset", "nature"])
    
    @patch("app.db.crud.create_photo")
    @patch("os.path.join")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    @patch("os.remove")
    async def test_create_photo_db_error(
        self, mock_remove, mock_exists, mock_file, mock_join, mock_create_photo,
        mock_upload_file, mock_db, mock_photographer_user
    ):
        """Test handling database errors during photo creation"""
        # Setup mocks
        mock_join.return_value = "/app/static/uploads/test.jpg"
        mock_exists.return_value = True
        mock_create_photo.side_effect = Exception("Database error")
        
        # Call the function and check for exception
        with pytest.raises(HTTPException) as exc_info:
            await create_photo(
                file=mock_upload_file,
                caption="Beautiful sunset",
                selected_tags="sunset, nature",
                db=mock_db,
                current_user=mock_photographer_user
            )
        
        # Verify exception details
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create photo" in exc_info.value.detail
        
        # Verify file was cleaned up
        mock_remove.assert_called_once_with("/app/static/uploads/test.jpg")
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.increment_download_count")
    @patch("os.path.join")
    @patch("os.path.isfile")
    @patch("fastapi.responses.FileResponse")
    async def test_download_photo_success(
        self, mock_file_response, mock_isfile, mock_join, mock_increment, mock_get_photo,
        mock_db, mock_current_user
    ):
        """Test successfully downloading a photo"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.id = 1
        mock_photo.filename = "test.jpg"
        mock_get_photo.return_value = mock_photo
        
        mock_join.return_value = "/app/static/uploads/test.jpg"
        mock_isfile.return_value = True
        
        mock_response = MagicMock()
        mock_file_response.return_value = mock_response
        
        # Call the function
        result = await download_photo(photo_id=1, db=mock_db, current_user=mock_current_user)
        
        # Verify result is the file response
        assert result == mock_response
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        mock_isfile.assert_called_once_with("/app/static/uploads/test.jpg")
        mock_increment.assert_called_once_with(mock_db, mock_photo)
        mock_file_response.assert_called_once_with(
            path="/app/static/uploads/test.jpg",
            media_type="application/octet-stream",
            filename="test.jpg"
        )
    
    @patch("app.db.crud.get_photo")
    async def test_download_photo_not_found(self, mock_get_photo, mock_db, mock_current_user):
        """Test downloading a photo that doesn't exist"""
        # Setup mock to return None (photo not found)
        mock_get_photo.return_value = None
        
        # Call the function and check for exception
        with pytest.raises(HTTPException) as exc_info:
            await download_photo(photo_id=999, db=mock_db, current_user=mock_current_user)
        
        # Verify exception details
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Photo not found"
        
        # Verify mock was called correctly
        mock_get_photo.assert_called_once_with(mock_db, 999)
    
    @patch("app.db.crud.get_photo")
    @patch("os.path.join")
    @patch("os.path.isfile")
    async def test_download_photo_file_missing(
        self, mock_isfile, mock_join, mock_get_photo,
        mock_db, mock_current_user
    ):
        """Test downloading a photo when the file is missing from storage"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.id = 1
        mock_photo.filename = "test.jpg"
        mock_get_photo.return_value = mock_photo
        
        mock_join.return_value = "/app/static/uploads/test.jpg"
        mock_isfile.return_value = False  # File doesn't exist
        
        # Call the function and check for exception
        with pytest.raises(HTTPException) as exc_info:
            await download_photo(photo_id=1, db=mock_db, current_user=mock_current_user)
        
        # Verify exception details
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Photo file not found on server"
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        mock_isfile.assert_called_once_with("/app/static/uploads/test.jpg")

    @patch("app.db.crud.get_feed_photos")
    @patch("app.config.settings")
    async def test_get_feed_success(
        self, mock_settings, mock_get_feed_photos,
        mock_db, mock_current_user
    ):
        """Test successfully retrieving the photo feed"""
        # Setup mocks
        mock_settings.BASE_URL = "http://testserver"
        
        mock_photo1 = MagicMock()
        mock_photo1.id = 1
        mock_photo1.filename = "test1.jpg"
        mock_photo1.caption = "Test photo 1"
        mock_photo1.user.username = "testuser"
        
        mock_photo2 = MagicMock()
        mock_photo2.id = 2
        mock_photo2.filename = "test2.jpg"
        mock_photo2.caption = "Test photo 2"
        mock_photo2.user.username = "testuser2"
        
        mock_get_feed_photos.return_value = [mock_photo1, mock_photo2]
        
        # Call the function
        result = await get_feed(
            page=1,
            limit=10,
            db=mock_db,
            current_user=mock_current_user
        )
        
        # Verify results
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].caption == "Test photo 1"
        assert result[0].username == "testuser"
        assert result[0].image_url == "http://testserver/static/uploads/test1.jpg"
        
        assert result[1].id == 2
        assert result[1].caption == "Test photo 2"
        assert result[1].username == "testuser2"
        assert result[1].image_url == "http://testserver/static/uploads/test2.jpg"
        
        # Verify mock was called correctly
        mock_get_feed_photos.assert_called_once_with(
            mock_db, skip=0, limit=10
        )

    @patch("app.db.crud.get_feed_photos")
    async def test_get_feed_empty(
        self, mock_get_feed_photos,
        mock_db, mock_current_user
    ):
        """Test retrieving an empty feed"""
        # Setup mock to return empty list
        mock_get_feed_photos.return_value = []
        
        # Call the function
        result = await get_feed(
            page=1, 
            limit=10, 
            db=mock_db, 
            current_user=mock_current_user
        )
        
        # Verify result is empty list
        assert result == []
        
        # Verify mock was called correctly
        mock_get_feed_photos.assert_called_once_with(
            mock_db, skip=0, limit=10
        )

    @patch("app.db.crud.get_photo")
    @patch("app.config.settings")
    async def test_get_share_link_success(
        self, mock_settings, mock_get_photo,
        mock_db, mock_current_user
    ):
        """Test successfully generating a share link"""
        # Setup mocks
        mock_settings.BASE_URL = "http://testserver"
        
        mock_photo = MagicMock()
        mock_photo.id = 1
        mock_photo.filename = "test.jpg"
        mock_get_photo.return_value = mock_photo
        
        # Call the function
        result = await get_share_link(
            photo_id=1,
            db=mock_db,
            current_user=mock_current_user
        )
        
        # Verify result
        assert result.share_url == "http://testserver/photos/1/view"
        
        # Verify mock was called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)

    @patch("app.db.crud.get_photo")
    async def test_get_share_link_not_found(
        self, mock_get_photo,
        mock_db, mock_current_user
    ):
        """Test generating a share link for a non-existent photo"""
        # Setup mock to return None (photo not found)
        mock_get_photo.return_value = None
        
        # Call the function and check for exception
        with pytest.raises(HTTPException) as exc_info:
            await get_share_link(
                photo_id=999,
                db=mock_db,
                current_user=mock_current_user
            )
        
        # Verify exception details
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Photo not found"
        
        # Verify mock was called correctly
        mock_get_photo.assert_called_once_with(mock_db, 999)