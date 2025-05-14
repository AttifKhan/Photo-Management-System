import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status

from app.routers.comment import create_comment, list_comments
from app.schemas.comment import CommentCreate

class TestCommentRoutes:
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.create_comment")
    def test_create_comment_as_photographer(self, mock_create_comment, mock_get_photo, mock_db, mock_photographer_user):
        """Test successful comment creation when user is the photographer"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = mock_photographer_user.id  # Same user as the photographer
        mock_get_photo.return_value = mock_photo
        
        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.user_id = mock_photographer_user.id
        mock_comment.photo_id = 1
        mock_comment.content = "Test comment"
        mock_create_comment.return_value = mock_comment
        
        # Create request data
        comment_data = CommentCreate(content="Test comment")
        
        # Call the function
        result = create_comment(photo_id=1, comment_in=comment_data, db=mock_db, current_user=mock_photographer_user)
        
        # Verify result
        assert result.id == 1
        assert result.content == "Test comment"
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        mock_create_comment.assert_called_once_with(
            mock_db, 
            user_id=mock_photographer_user.id, 
            photo_id=1, 
            content="Test comment"
        )
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    @patch("app.db.crud.create_comment")
    def test_create_comment_as_follower(self, mock_create_comment, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test successful comment creation when user follows the photographer"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the commenter
        mock_get_photo.return_value = mock_photo
        
        # User follows the photographer
        mock_check_follow.return_value = True
        
        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.user_id = mock_current_user.id
        mock_comment.photo_id = 1
        mock_comment.content = "Test comment"
        mock_create_comment.return_value = mock_comment
        
        # Create request data
        comment_data = CommentCreate(content="Test comment")
        
        # Call the function
        result = create_comment(photo_id=1, comment_in=comment_data, db=mock_db, current_user=mock_current_user)
        
        # Verify result
        assert result.id == 1
        assert result.content == "Test comment"
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Updated to match actual call format in the comment.py file
        mock_check_follow.assert_called_once_with(
            mock_db, 
            follower_id=mock_current_user.id, 
            followee_id=2
        )
        mock_create_comment.assert_called_once_with(
            mock_db, 
            user_id=mock_current_user.id, 
            photo_id=1, 
            content="Test comment"
        )
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    def test_create_comment_permission_denied(self, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test comment creation fails when user has no permission"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the commenter
        mock_get_photo.return_value = mock_photo
        
        # User does not follow the photographer
        mock_check_follow.return_value = False
        
        # Create request data
        comment_data = CommentCreate(content="Test comment")
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            create_comment(photo_id=1, comment_in=comment_data, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "You can only comment on photos posted by photographers you follow or your own photos" in exc_info.value.detail
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Updated to match actual call format in the comment.py file
        mock_check_follow.assert_called_once_with(
            mock_db, 
            follower_id=mock_current_user.id, 
            followee_id=2
        )
    
    @patch("app.db.crud.get_photo")
    def test_create_comment_photo_not_found(self, mock_get_photo, mock_db, mock_current_user):
        """Test comment creation when photo doesn't exist"""
        # Setup mock to return None (photo not found)
        mock_get_photo.return_value = None
        
        comment_data = CommentCreate(content="Test comment")
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            create_comment(photo_id=999, comment_in=comment_data, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Photo not found"
        
        # Verify mock was called correctly
        mock_get_photo.assert_called_once_with(mock_db, 999)
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.get_comments_by_photo")
    def test_list_comments_as_photographer(self, mock_get_comments, mock_get_photo, mock_db, mock_photographer_user):
        """Test listing comments for a photo as the photographer who posted it"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = mock_photographer_user.id  # Same user as the photographer
        mock_get_photo.return_value = mock_photo
        
        mock_comment1 = MagicMock()
        mock_comment1.id = 1
        mock_comment1.content = "First comment"
        
        mock_comment2 = MagicMock()
        mock_comment2.id = 2
        mock_comment2.content = "Second comment"
        
        mock_get_comments.return_value = [mock_comment1, mock_comment2]
        
        # Call the function
        result = list_comments(photo_id=1, db=mock_db, current_user=mock_photographer_user)
        
        # Verify result
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].content == "First comment"
        assert result[1].id == 2
        assert result[1].content == "Second comment"
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        mock_get_comments.assert_called_once_with(mock_db, 1)
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    @patch("app.db.crud.get_comments_by_photo")
    def test_list_comments_as_follower(self, mock_get_comments, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test listing comments for a photo as a follower of the photographer"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the viewer
        mock_get_photo.return_value = mock_photo
        
        # User follows the photographer
        mock_check_follow.return_value = True
        
        mock_comment1 = MagicMock()
        mock_comment1.id = 1
        mock_comment1.content = "First comment"
        
        mock_comment2 = MagicMock()
        mock_comment2.id = 2
        mock_comment2.content = "Second comment"
        
        mock_get_comments.return_value = [mock_comment1, mock_comment2]
        
        # Call the function
        result = list_comments(photo_id=1, db=mock_db, current_user=mock_current_user)
        
        # Verify result
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].content == "First comment"
        assert result[1].id == 2
        assert result[1].content == "Second comment"
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Updated to match actual call format in the comment.py file
        mock_check_follow.assert_called_once_with(
            mock_db, 
            follower_id=mock_current_user.id, 
            followee_id=2
        )
        mock_get_comments.assert_called_once_with(mock_db, 1)
    
    @patch("app.db.crud.get_photo")
    @patch("app.db.crud.check_follow_exists")
    def test_list_comments_permission_denied(self, mock_check_follow, mock_get_photo, mock_db, mock_current_user):
        """Test listing comments fails when user has no permission"""
        # Setup mocks
        mock_photo = MagicMock()
        mock_photo.user_id = 2  # Different user than the viewer
        mock_get_photo.return_value = mock_photo
        
        # User does not follow the photographer
        mock_check_follow.return_value = False
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            list_comments(photo_id=1, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "You can only view comments on photos posted by photographers you follow or your own photos" in exc_info.value.detail
        
        # Verify mocks were called correctly
        mock_get_photo.assert_called_once_with(mock_db, 1)
        # Updated to match actual call format in the comment.py file
        mock_check_follow.assert_called_once_with(
            mock_db, 
            follower_id=mock_current_user.id, 
            followee_id=2
        )
    
    @patch("app.db.crud.get_photo")
    def test_list_comments_photo_not_found(self, mock_get_photo, mock_db, mock_current_user):
        """Test listing comments when photo doesn't exist"""
        # Setup mock to return None (photo not found)
        mock_get_photo.return_value = None
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            list_comments(photo_id=999, db=mock_db, current_user=mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Photo not found"
        
        # Verify mock was called correctly
        mock_get_photo.assert_called_once_with(mock_db, 999)