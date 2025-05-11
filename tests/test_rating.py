import pytest
from fastapi import HTTPException, status
from unittest.mock import MagicMock, patch

from app.schemas.rating import RatingCreate, RatingOut
from app.routers.rating import create_rating, list_ratings, average_rating

class TestRatingRoutes:
    def test_create_rating_success(self, mock_db, mock_current_user):
        # Arrange
        photo_id = 1
        test_photo = MagicMock()
        mock_db.query().filter().first.return_value = test_photo
        
        rating_in = RatingCreate(score=4)
        mock_rating = MagicMock(id=1, user_id=mock_current_user.id, photo_id=photo_id, score=4)
        mock_db.crud.create_rating.return_value = mock_rating
        
        # Mock crud methods
        with patch("app.db.crud.get_photo", return_value=test_photo), \
             patch("app.db.crud.create_rating", return_value=mock_rating):
            
            # Act
            result = create_rating(photo_id, rating_in, mock_db, mock_current_user)
            
            # Assert
            assert result == mock_rating
            
    def test_create_rating_photo_not_found(self, mock_db, mock_current_user):
        # Arrange
        photo_id = 999  # Non-existent photo
        rating_in = RatingCreate(score=4)
        
        # Mock crud method to return None (photo not found)
        with patch("app.db.crud.get_photo", return_value=None):
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                create_rating(photo_id, rating_in, mock_db, mock_current_user)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert exc_info.value.detail == "Photo not found"
    
    def test_list_ratings_success(self, mock_db):
        # Arrange
        photo_id = 1
        test_photo = MagicMock()
        test_ratings = [
            MagicMock(id=1, user_id=1, photo_id=photo_id, score=4),
            MagicMock(id=2, user_id=2, photo_id=photo_id, score=5)
        ]
        
        # Mock crud methods
        with patch("app.db.crud.get_photo", return_value=test_photo), \
             patch("app.db.crud.get_ratings_by_photo", return_value=test_ratings):
            
            # Act
            result = list_ratings(photo_id, mock_db)
            
            # Assert
            assert result == test_ratings
    
    def test_list_ratings_photo_not_found(self, mock_db):
        # Arrange
        photo_id = 999  # Non-existent photo
        
        # Mock crud method to return None (photo not found)
        with patch("app.db.crud.get_photo", return_value=None):
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                list_ratings(photo_id, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert exc_info.value.detail == "Photo not found"
    
    def test_average_rating_success(self, mock_db):
        # Arrange
        photo_id = 1
        test_photo = MagicMock()
        average = 4.5
        
        # Mock crud methods
        with patch("app.db.crud.get_photo", return_value=test_photo), \
             patch("app.db.crud.get_average_rating", return_value=average):
            
            # Act
            result = average_rating(photo_id, mock_db)
            
            # Assert
            assert result == average
    
    def test_average_rating_photo_not_found(self, mock_db):
        # Arrange
        photo_id = 999  # Non-existent photo
        
        # Mock crud method to return None (photo not found)
        with patch("app.db.crud.get_photo", return_value=None):
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                average_rating(photo_id, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert exc_info.value.detail == "Photo not found"