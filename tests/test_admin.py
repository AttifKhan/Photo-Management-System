import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.routers.admin import router, require_admin
from app.db.models import User, Photo, Comment


class TestAdminDependency:
    def test_require_admin_success(self, mock_admin_user):
        """Test that require_admin passes with admin user"""
        result = require_admin(mock_admin_user)
        assert result == mock_admin_user

    def test_require_admin_failure(self, mock_current_user):
        """Test that require_admin raises 403 with non-admin user"""
        with pytest.raises(HTTPException) as excinfo:
            require_admin(mock_current_user)
        assert excinfo.value.status_code == 403


class TestAdminRoutes:
    @patch("app.routers.admin.crud")
    def test_list_users(self, mock_crud, mock_db, mock_admin_user):
        """Test listing all users"""
        mock_users = [MagicMock(spec=User) for _ in range(3)]
        mock_db.query.return_value.all.return_value = mock_users

        # Call the endpoint function directly instead of using url_path_for
        result = router.routes[0].endpoint(
            db=mock_db,
            admin_user=mock_admin_user
        )

        # Verify query was called
        mock_db.query.assert_called_once()
        assert mock_db.query.return_value.all.called
        
        # Check result
        assert result == mock_users
        assert len(result) == 3

    @patch("app.routers.admin.crud")
    def test_delete_user_success(self, mock_crud, mock_db, mock_admin_user):
        """Test deleting a user successfully"""
        user_id = 4
        mock_user = MagicMock(spec=User)
        mock_crud.get_user_by_id.return_value = mock_user

        # Call the endpoint function directly
        result = router.routes[1].endpoint(
            user_id=user_id,
            db=mock_db,
            admin_user=mock_admin_user
        )

        # Verify mock calls
        mock_crud.get_user_by_id.assert_called_once_with(mock_db, user_id)
        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
        
        # Check result
        assert result.detail == f"User {user_id} deleted"

    @patch("app.routers.admin.crud")
    def test_delete_user_not_found(self, mock_crud, mock_db, mock_admin_user):
        """Test deleting a non-existent user"""
        user_id = 999
        mock_crud.get_user_by_id.return_value = None

        # Call the endpoint function directly
        with pytest.raises(HTTPException) as excinfo:
            router.routes[1].endpoint(
                user_id=user_id,
                db=mock_db,
                admin_user=mock_admin_user
            )
        
        # Verify exception
        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "User not found"
        
        # Verify mock calls
        mock_crud.get_user_by_id.assert_called_once_with(mock_db, user_id)
        assert not mock_db.delete.called
        assert not mock_db.commit.called

    @patch("app.routers.admin.crud")
    def test_list_photos(self, mock_crud, mock_db, mock_admin_user):
        """Test listing all photos"""
        mock_photos = [MagicMock(spec=Photo) for _ in range(3)]
        mock_db.query.return_value.all.return_value = mock_photos

        # Call the endpoint function directly
        result = router.routes[2].endpoint(
            db=mock_db,
            admin_user=mock_admin_user
        )

        # Verify query was called
        mock_db.query.assert_called_once()
        assert mock_db.query.return_value.all.called
        
        # Check result
        assert result == mock_photos
        assert len(result) == 3

    @patch("app.routers.admin.crud")
    def test_delete_photo_success(self, mock_crud, mock_db, mock_admin_user):
        """Test deleting a photo successfully"""
        photo_id = 5
        mock_photo = MagicMock(spec=Photo)
        mock_crud.get_photo.return_value = mock_photo

        # Call the endpoint function directly
        result = router.routes[3].endpoint(
            photo_id=photo_id,
            db=mock_db,
            admin_user=mock_admin_user
        )

        # Verify mock calls
        mock_crud.get_photo.assert_called_once_with(mock_db, photo_id)
        mock_db.delete.assert_called_once_with(mock_photo)
        mock_db.commit.assert_called_once()
        
        # Check result
        assert result.detail == f"Photo {photo_id} deleted"

    @patch("app.routers.admin.crud")
    def test_delete_photo_not_found(self, mock_crud, mock_db, mock_admin_user):
        """Test deleting a non-existent photo"""
        photo_id = 999
        mock_crud.get_photo.return_value = None

        # Call the endpoint function directly
        with pytest.raises(HTTPException) as excinfo:
            router.routes[3].endpoint(
                photo_id=photo_id,
                db=mock_db,
                admin_user=mock_admin_user
            )
        
        # Verify exception
        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "Photo not found"
        
        # Verify mock calls
        mock_crud.get_photo.assert_called_once_with(mock_db, photo_id)
        assert not mock_db.delete.called
        assert not mock_db.commit.called

    @patch("app.routers.admin.crud")
    def test_list_comments(self, mock_crud, mock_db, mock_admin_user):
        """Test listing all comments"""
        mock_comments = [MagicMock(spec=Comment) for _ in range(3)]
        mock_db.query.return_value.all.return_value = mock_comments

        # Call the endpoint function directly
        result = router.routes[4].endpoint(
            db=mock_db,
            admin_user=mock_admin_user
        )

        # Verify query was called
        mock_db.query.assert_called_once()
        assert mock_db.query.return_value.all.called
        
        # Check result
        assert result == mock_comments
        assert len(result) == 3

    @patch("app.routers.admin.crud")
    def test_delete_comment_success(self, mock_crud, mock_db, mock_admin_user):
        """Test deleting a comment successfully"""
        comment_id = 6
        mock_comment = MagicMock(spec=Comment)
        # This simulates the current issue in your code
        mock_crud.get_comments_by_photo.return_value = [mock_comment]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_comment

        # Call the endpoint function directly
        result = router.routes[5].endpoint(
            comment_id=comment_id,
            db=mock_db,
            admin_user=mock_admin_user
        )

        # Verify direct CommentModel query was called
        mock_db.query.assert_called_once()
        mock_db.query.return_value.filter.assert_called_once()
        mock_db.query.return_value.filter.return_value.first.assert_called_once()
        
        # Verify object was deleted
        mock_db.delete.assert_called_once_with(mock_comment)
        mock_db.commit.assert_called_once()
        
        # Check result
        assert result.detail == f"Comment {comment_id} deleted"

    @patch("app.routers.admin.crud")
    def test_delete_comment_not_found(self, mock_crud, mock_db, mock_admin_user):
        """Test deleting a non-existent comment"""
        comment_id = 999
        # Simulate that the comment is not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Call the endpoint function directly
        with pytest.raises(HTTPException) as excinfo:
            router.routes[5].endpoint(
                comment_id=comment_id,
                db=mock_db,
                admin_user=mock_admin_user
            )
        
        # Verify exception
        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "Comment not found"
        
        # Verify object was not deleted
        assert not mock_db.delete.called
        assert not mock_db.commit.called