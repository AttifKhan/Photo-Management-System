import pytest
from unittest.mock import patch, MagicMock, ANY
from fastapi import HTTPException, status

from app.routers.rating import create_rating, list_ratings, average_rating
from app.schemas.rating import RatingCreate

class TestRatingRoutes:
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.create_rating")
    def test_create_rating_as_photographer(self, mock_create_rating, mock_get_photo, mock_db, mock_photographer_user):
        """Test successful rating creation when user is the photographer"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = mock_photographer_user.id  # Same user as the photographer
        mock_get_photo.return_value = mock_photo
        
        mock_rating = MagicMock()
        mock_rating.id = 1
        mock_rating.user_id = mock_photographer_user.id
        mock_rating.photo_id = 1
        mock_rating.score = 4
        mock_create_rating.return_value = mock_rating
        
        # Create request data
        rating_data = RatingCreate(score=4)
        
        # Call the function
        result = create_rating(photo_id=1, rating_in=rating_data, db=mock_db, current_user=mock_photographer_user)
        
        # Verify result
        assert result.id == 1
        assert result.score == 4
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        mock_create_rating.assert_called_once_with(
            mock_db, 
            user_id=mock_photographer_user.id, 
            photo_id=1, 
            score=4
        )
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    @patch("app.db.crud.create_rating")
    def test_create_rating_as_follower(self, mock_create_rating, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test successful rating creation when user follows the photographer"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the rater
        mock_get_photo.return_value = mock_photo
        
        # User follows the photographer
        mock_check_follow.return_value = True
        
        mock_rating = MagicMock()
        mock_rating.id = 1
        mock_rating.user_id = mock_current_user.id
        mock_rating.photo_id = 1
        mock_rating.score = 5
        mock_create_rating.return_value = mock_rating
        
        # Create request data
        rating_data = RatingCreate(score=5)
        
        # Call the function
        result = create_rating(photo_id=1, rating_in=rating_data, db=mock_db, current_user=mock_current_user)
        
        # Verify result
        assert result.id == 1
        assert result.score == 5
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Fix: Use ANY for positional arguments
        mock_check_follow.assert_called_once_with(
            ANY,  # db is passed positionally 
            follower_id=mock_current_user.id, 
            followee_id=2
        )
        mock_create_rating.assert_called_once_with(
            mock_db, 
            user_id=mock_current_user.id, 
            photo_id=1, 
            score=5
        )
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    def test_create_rating_permission_denied(self, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test rating creation fails when user has no permission"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the rater
        mock_get_photo.return_value = mock_photo
        
        # User does not follow the photographer
        mock_check_follow.return_value = False
        
        # Create request data
        rating_data = RatingCreate(score=3)
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            create_rating(photo_id=1, rating_in=rating_data, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "You can only rate photos posted by photographers you follow or your own photos" in exc_info.value.detail
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Fix: Use ANY for positional arguments
        mock_check_follow.assert_called_once_with(
            ANY,  # db is passed positionally
            follower_id=mock_current_user.id, 
            followee_id=2
        )
    
    @patch("app.db.crud.get_photo")
    def test_create_rating_photo_not_found(self, mock_get_photo, mock_db, mock_current_user):
        """Test rating creation when photo doesn't exist"""
        # Setup mock to return None (photo not found)
        mock_get_photo.return_value = None
        
        rating_data = RatingCreate(score=4)
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            create_rating(photo_id=999, rating_in=rating_data, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Photo not found"
        
        # Verify mock was called correctly
        mock_get_photo.assert_called_once_with(mock_db, 999)
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.get_ratings_by_photo")
    def test_list_ratings_as_photographer(self, mock_get_ratings, mock_get_photo, mock_db, mock_photographer_user):
        """Test listing ratings for a photo as the photographer who posted it"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = mock_photographer_user.id  # Same user as the photographer
        mock_get_photo.return_value = mock_photo
        
        mock_rating1 = MagicMock()
        mock_rating1.id = 1
        mock_rating1.score = 4
        
        mock_rating2 = MagicMock()
        mock_rating2.id = 2
        mock_rating2.score = 5
        
        mock_get_ratings.return_value = [mock_rating1, mock_rating2]
        
        # Call the function
        result = list_ratings(photo_id=1, db=mock_db, current_user=mock_photographer_user)
        
        # Verify result
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].score == 4
        assert result[1].id == 2
        assert result[1].score == 5
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        mock_get_ratings.assert_called_once_with(mock_db, 1)
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    @patch("app.db.crud.get_ratings_by_photo")
    def test_list_ratings_as_follower(self, mock_get_ratings, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test listing ratings for a photo as a follower of the photographer"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the viewer
        mock_get_photo.return_value = mock_photo
        
        # User follows the photographer
        mock_check_follow.return_value = True
        
        mock_rating1 = MagicMock()
        mock_rating1.id = 1
        mock_rating1.score = 4
        
        mock_rating2 = MagicMock()
        mock_rating2.id = 2
        mock_rating2.score = 5
        
        mock_get_ratings.return_value = [mock_rating1, mock_rating2]
        
        # Call the function
        result = list_ratings(photo_id=1, db=mock_db, current_user=mock_current_user)
        
        # Verify result
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].score == 4
        assert result[1].id == 2
        assert result[1].score == 5
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Fix: Use ANY for positional arguments
        mock_check_follow.assert_called_once_with(
            ANY,  # db is passed positionally
            follower_id=mock_current_user.id, 
            followee_id=2
        )
        mock_get_ratings.assert_called_once_with(mock_db, 1)
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    def test_list_ratings_permission_denied(self, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test listing ratings fails when user has no permission"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the viewer
        mock_get_photo.return_value = mock_photo
        
        # User does not follow the photographer
        mock_check_follow.return_value = False
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            list_ratings(photo_id=1, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "You can only view ratings on photos posted by photographers you follow or your own photos" in exc_info.value.detail
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Fix: Use ANY for positional arguments
        mock_check_follow.assert_called_once_with(
            ANY,  # db is passed positionally
            follower_id=mock_current_user.id, 
            followee_id=2
        )
    
    @patch("app.db.crud.get_photo")
    def test_list_ratings_photo_not_found(self, mock_get_photo, mock_db, mock_current_user):
        """Test listing ratings when photo doesn't exist"""
        # Setup mock to return None (photo not found)
        mock_get_photo.return_value = None
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            list_ratings(photo_id=999, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Photo not found"
        
        # Verify mock was called correctly
        mock_get_photo.assert_called_once_with(mock_db, 999)
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.get_average_rating")
    def test_average_rating_as_photographer(self, mock_get_average, mock_get_photo, mock_db, mock_photographer_user):
        """Test getting average rating as the photographer who posted the photo"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = mock_photographer_user.id  # Same user as the photographer
        mock_get_photo.return_value = mock_photo
        
        # Average rating value
        mock_get_average.return_value = 4.5
        
        # Call the function
        result = average_rating(photo_id=1, db=mock_db, current_user=mock_photographer_user)
        
        # Verify result
        assert result == 4.5
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        mock_get_average.assert_called_once_with(mock_db, 1)
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    @patch("app.db.crud.get_average_rating")
    def test_average_rating_as_follower(self, mock_get_average, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test getting average rating as a follower of the photographer"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the viewer
        mock_get_photo.return_value = mock_photo
        
        # User follows the photographer
        mock_check_follow.return_value = True
        
        # Average rating value
        mock_get_average.return_value = 4.5
        
        # Call the function
        result = average_rating(photo_id=1, db=mock_db, current_user=mock_current_user)
        
        # Verify result
        assert result == 4.5
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Fix: Use ANY for positional arguments
        mock_check_follow.assert_called_once_with(
            ANY,  # db is passed positionally
            follower_id=mock_current_user.id, 
            followee_id=2
        )
        mock_get_average.assert_called_once_with(mock_db, 1)
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    def test_average_rating_permission_denied(self, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test getting average rating fails when user has no permission"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the viewer
        mock_get_photo.return_value = mock_photo
        
        # User does not follow the photographer
        mock_check_follow.return_value = False
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            average_rating(photo_id=1, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "You can only view average ratings on photos posted by photographers you follow or your own photos" in exc_info.value.detail
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Fix: Use ANY for positional arguments
        mock_check_follow.assert_called_once_with(
            ANY,  # db is passed positionally
            follower_id=mock_current_user.id, 
            followee_id=2
        )
    
    @patch("app.db.crud.get_photo")
    def test_average_rating_photo_not_found(self, mock_get_photo, mock_db, mock_current_user):
        """Test getting average rating when photo doesn't exist"""
        # Setup mock to return None (photo not found)
        mock_get_photo.return_value = None
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            average_rating(photo_id=999, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Photo not found"
        
        # Verify mock was called correctly
        mock_get_photo.assert_called_once_with(mock_db, 999)