import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status

from app.routers.follow import follow_photographer, unfollow_photographer, list_followees, list_followers

class TestFollowRoutes:
    @patch("app.db.crud.get_user_by_id")
    @patch("app.db.crud.get_follow")
    @patch("app.db.crud.follow_user")
    def test_follow_photographer_success(self, mock_follow_user, mock_get_follow, mock_get_user, mock_db, mock_current_user):
        """Test successfully following a photographer"""
        # Setup mocks
        mock_photographer = MagicMock()
        mock_photographer.id = 2
        mock_photographer.is_photographer = True
        mock_get_user.return_value = mock_photographer
        
        # No existing follow relationship
        mock_get_follow.return_value = None
        
        # New follow relationship
        mock_follow = MagicMock()
        mock_follow.follower_id = mock_current_user.id
        mock_follow.followee_id = 2
        mock_follow_user.return_value = mock_follow
        
        # Call the function
        result = follow_photographer(photographer_id=2, db=mock_db, current_user=mock_current_user)
        
        # Verify the result
        assert result.follower_id == mock_current_user.id
        assert result.followee_id == 2
        
        # Verify mocks were called correctly
        mock_get_user.assert_called_once_with(mock_db, 2)
        mock_get_follow.assert_called_once_with(mock_db, mock_current_user.id, 2)
        mock_follow_user.assert_called_once_with(mock_db, mock_current_user.id, 2)
    
    @patch("app.db.crud.get_user_by_id")
    def test_follow_yourself(self, mock_get_user, mock_db, mock_current_user):
        """Test trying to follow yourself"""
        # Set up mock current user to have the same ID as the target
        mock_current_user.id = 1
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            follow_photographer(photographer_id=1, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Cannot follow yourself"
        
        # Verify mock was not called
        mock_get_user.assert_not_called()
    
    @patch("app.db.crud.get_user_by_id")
    def test_follow_nonexistent_user(self, mock_get_user, mock_db, mock_current_user):
        """Test following a user that doesn't exist"""
        # Setup mock to return None (user not found)
        mock_get_user.return_value = None
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            follow_photographer(photographer_id=999, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Photographer not found"
        
        # Verify mock was called correctly
        mock_get_user.assert_called_once_with(mock_db, 999)
    
    @patch("app.db.crud.get_user_by_id")
    def test_follow_non_photographer(self, mock_get_user, mock_db, mock_current_user):
        """Test following a user who is not a photographer"""
        # Setup mock to return a non-photographer user
        mock_user = MagicMock()
        mock_user.id = 3
        mock_user.is_photographer = False
        mock_get_user.return_value = mock_user
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            follow_photographer(photographer_id=3, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "You can only follow photographers"
        
        # Verify mock was called correctly
        mock_get_user.assert_called_once_with(mock_db, 3)
    
    @patch("app.db.crud.get_user_by_id")
    @patch("app.db.crud.get_follow")
    def test_follow_already_following(self, mock_get_follow, mock_get_user, mock_db, mock_current_user):
        """Test attempting to follow a photographer you already follow"""
        # Setup mocks
        mock_photographer = MagicMock()
        mock_photographer.id = 2
        mock_photographer.is_photographer = True
        mock_get_user.return_value = mock_photographer
        
        # Set up existing follow relationship
        mock_get_follow.return_value = MagicMock()
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            follow_photographer(photographer_id=2, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "You are already following this photographer"
        
        # Verify mocks were called correctly
        mock_get_user.assert_called_once_with(mock_db, 2)
        mock_get_follow.assert_called_once_with(mock_db, mock_current_user.id, 2)
    
    @patch("app.db.crud.get_user_by_id")
    @patch("app.db.crud.check_follow_exists")
    @patch("app.db.crud.unfollow_user")
    def test_unfollow_photographer_success(self, mock_unfollow_user, mock_check_follow, mock_get_user, mock_db, mock_current_user):
        """Test successfully unfollowing a photographer"""
        # Setup mocks
        mock_photographer = MagicMock()
        mock_photographer.id = 2
        mock_photographer.is_photographer = True
        mock_get_user.return_value = mock_photographer
        
        # Existing follow relationship
        mock_check_follow.return_value = True
        
        # Call the function
        result = unfollow_photographer(photographer_id=2, db=mock_db, current_user=mock_current_user)
        
        # Verify result is None (204 No Content)
        assert result is None
        
        # Verify mocks were called correctly
        mock_get_user.assert_called_once_with(mock_db, 2)
        mock_check_follow.assert_called_once_with(mock_db, mock_current_user.id, 2)
        mock_unfollow_user.assert_called_once_with(mock_db, mock_current_user.id, 2)
    
    @patch("app.db.crud")
    def test_list_followees(self, mock_crud, mock_db, mock_current_user):
        """Test listing photographers a user follows"""
        # Setup mock
        follow1 = MagicMock()
        follow1.follower_id = mock_current_user.id
        follow1.followee_id = 2
        
        follow2 = MagicMock()
        follow2.follower_id = mock_current_user.id
        follow2.followee_id = 3
        
        # Make the query object return our mock follows when filtered
        mock_db.query.return_value.filter.return_value.all.return_value = [follow1, follow2]
        
        # Call the function
        result = list_followees(db=mock_db, current_user=mock_current_user)
        
        # Verify the result
        assert result["count"] == 2
        assert len(result["followees"]) == 2
        
        # Verify mock was called correctly
        mock_db.query.assert_called_once()

    @patch("app.db.crud")
    def test_list_followers_as_photographer(self, mock_crud, mock_db, mock_photographer_user):
        """Test listing followers as a photographer"""
        # Setup mock
        follow1 = MagicMock()
        follow1.follower_id = 1
        follow1.followee_id = mock_photographer_user.id
        
        follow2 = MagicMock()
        follow2.follower_id = 3
        follow2.followee_id = mock_photographer_user.id
        
        # Make the query object return our mock follows when filtered
        mock_db.query.return_value.filter.return_value.all.return_value = [follow1, follow2]
        
        # Call the function
        result = list_followers(db=mock_db, current_user=mock_photographer_user)
        
        # Verify the result
        assert result["count"] == 2
        assert len(result["followers"]) == 2
        
        # Verify mock was called correctly
        mock_db.query.assert_called_once()
    
    def test_list_followers_as_non_photographer(self, mock_db, mock_current_user):
        """Test listing followers as a non-photographer (should fail)"""
        # Ensure current user is not a photographer
        mock_current_user.is_photographer = False
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            list_followers(db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Only photographers can view their followers"