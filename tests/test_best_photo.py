import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from fastapi import HTTPException

from app.routers.best_photo import best_photo_today
from app.schemas.best_photo import BestPhotoOut

class TestBestPhotoRoute:
    @patch("app.db.crud.get_best_photo_of_day")
    @patch("app.db.crud.calculate_and_store_best_photo")
    async def test_best_photo_today_existing(self, mock_calculate, mock_get_best, mock_db, mock_current_user):
        """Test getting the best photo of the day when it already exists in DB"""
        # Setup the mock to return a record
        mock_record = MagicMock()
        mock_record.photo = "test_photo.jpg"
        mock_record.date = date.today()
        mock_get_best.return_value = mock_record
        
        # Call the function
        result = await best_photo_today(db=mock_db, current_user=mock_current_user)
        
        # Verify the result
        assert isinstance(result, BestPhotoOut)
        assert result.photo == "test_photo.jpg"
        assert result.date == date.today()
        
        # Verify mocks were called correctly
        mock_get_best.assert_called_once_with(mock_db, date.today())
        mock_calculate.assert_not_called()
    
    @patch("app.db.crud.get_best_photo_of_day")
    @patch("app.db.crud.calculate_and_store_best_photo")
    async def test_best_photo_today_calculate_new(self, mock_calculate, mock_get_best, mock_db, mock_current_user):
        """Test calculating and storing a new best photo when none exists"""
        # Setup mock for initial check to return None (no existing record)
        mock_get_best.return_value = None
        
        # Setup mock for calculation to return a valid record
        mock_record = MagicMock()
        mock_record.photo = "calculated_best.jpg"
        mock_record.date = date.today()
        mock_calculate.return_value = mock_record
        
        # Call the function
        result = await best_photo_today(db=mock_db, current_user=mock_current_user)
        
        # Verify the result
        assert isinstance(result, BestPhotoOut)
        assert result.photo == "calculated_best.jpg"
        assert result.date == date.today()
        
        # Verify mocks were called correctly
        mock_get_best.assert_called_once_with(mock_db, date.today())
        mock_calculate.assert_called_once_with(mock_db, date.today())
    
    @patch("app.db.crud.get_best_photo_of_day")
    @patch("app.db.crud.calculate_and_store_best_photo")
    async def test_best_photo_today_no_photos(self, mock_calculate, mock_get_best, mock_db, mock_current_user):
        """Test handling case when no photos are available for today"""
        # Setup mocks to return None (no photos available)
        mock_get_best.return_value = None
        mock_calculate.return_value = None
        
        # Call the function and check it raises the expected exception
        with pytest.raises(HTTPException) as exc_info:
            await best_photo_today(db=mock_db, current_user=mock_current_user)
        
        # Verify the exception details
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "No photos available for today"
        
        # Verify mocks were called correctly
        mock_get_best.assert_called_once_with(mock_db, date.today())
        mock_calculate.assert_called_once_with(mock_db, date.today())