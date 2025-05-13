import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from fastapi import HTTPException

from app.routers.best_photo import best_photo_today
from app.schemas.best_photo import BestPhotoOut
from app.schemas.photo import PhotoOut

class TestBestPhotoRoute:
    @patch("app.db.crud.get_best_photo_of_day")
    @patch("app.db.crud.calculate_and_store_best_photo")
    @pytest.mark.asyncio
    async def test_best_photo_today_existing(self, mock_calculate, mock_get_best, mock_db, mock_current_user):
        """Test getting the best photo of the day when it already exists in DB"""
        # Setup a more complete mock photo object
        mock_photo = MagicMock()
        mock_photo.id = 1
        mock_photo.user_id = 1
        mock_photo.owner = MagicMock()
        mock_photo.owner.username = "test_user"
        mock_photo.filename = "test_photo.jpg"
        mock_photo.caption = "Test caption"
        mock_photo.upload_time = datetime.now()
        mock_photo.download_count = 0
        mock_photo.tags = []
        mock_photo.ratings = []
        mock_photo.comments = []
        
        # Setup the mock record
        mock_record = MagicMock()
        mock_record.photo = mock_photo  # Use the photo object instead of just a string
        mock_record.date = date.today()
        mock_get_best.return_value = mock_record
        
        # Call the function
        result = await best_photo_today(db=mock_db, current_user=mock_current_user)
        
        # Verify the result
        assert isinstance(result, BestPhotoOut)
        assert isinstance(result.photo, PhotoOut)
        assert result.photo.filename == "test_photo.jpg"
        assert result.date == date.today()
        
        # Verify mocks were called correctly
        mock_get_best.assert_called_once_with(mock_db, date.today())
        mock_calculate.assert_not_called()
    
    @patch("app.db.crud.get_best_photo_of_day")
    @patch("app.db.crud.calculate_and_store_best_photo")
    @pytest.mark.asyncio
    async def test_best_photo_today_calculate_new(self, mock_calculate, mock_get_best, mock_db, mock_current_user):
        """Test calculating and storing a new best photo when none exists"""
        # Setup mock for initial check to return None (no existing record)
        mock_get_best.return_value = None
        
        # Setup a more complete mock photo object
        mock_photo = MagicMock()
        mock_photo.id = 2
        mock_photo.user_id = 1
        mock_photo.owner = MagicMock()
        mock_photo.owner.username = "test_user"
        mock_photo.filename = "calculated_best.jpg"
        mock_photo.caption = "Calculated best photo"
        mock_photo.upload_time = datetime.now()
        mock_photo.download_count = 0
        mock_photo.tags = []
        mock_photo.ratings = []
        mock_photo.comments = []
        
        # Setup mock for calculation to return a valid record
        mock_record = MagicMock()
        mock_record.photo = mock_photo  # Use the photo object instead of just a string
        mock_record.date = date.today()
        mock_calculate.return_value = mock_record
        
        # Call the function
        result = await best_photo_today(db=mock_db, current_user=mock_current_user)
        
        # Verify the result
        assert isinstance(result, BestPhotoOut)
        assert isinstance(result.photo, PhotoOut)
        assert result.photo.filename == "calculated_best.jpg"
        assert result.date == date.today()
        
        # Verify mocks were called correctly
        mock_get_best.assert_called_once_with(mock_db, date.today())
        mock_calculate.assert_called_once_with(mock_db, date.today())