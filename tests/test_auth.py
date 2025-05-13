import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.routers.auth import router
from app.schemas.user import UserCreate
from app.schemas.auth import Token
from app.core.security import verify_password, create_access_token  # Add these imports


class TestAuthRoutes:
    @patch("app.routers.auth.crud")
    @patch("app.routers.auth.hash_password")
    def test_register_user_success(self, mock_hash_password, mock_crud, mock_db):
        """Test successful user registration"""
        # Setup test data
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "is_photographer": True,
            "is_admin": False
        }
        user_in = UserCreate(**user_data)
        
        # Mock functions
        mock_hash_password.return_value = "hashed_password"
        mock_crud.get_user_by_email.return_value = None  # Email not registered
        mock_crud.get_user_by_username.return_value = None 
        mock_user = MagicMock()
        mock_crud.create_user.return_value = mock_user
        
        # Call the endpoint
        result = router.routes[0].endpoint(
            user_in=user_in,
            db=mock_db
        )
        
        # Verify mock calls
        mock_crud.get_user_by_email.assert_called_once_with(mock_db, user_in.email)
        mock_hash_password.assert_called_once_with(user_in.password)
        mock_crud.create_user.assert_called_once_with(
            mock_db,
            username=user_in.username,
            email=user_in.email,
            hashed_password="hashed_password",
            is_photographer=user_in.is_photographer,
            is_admin=user_in.is_admin
        )
        
        # Check result
        assert result == mock_user

        @patch("app.routers.auth.crud")
        def test_register_user_username_exists(self, mock_crud, mock_db):
            """Test registration with existing username"""
            # Setup test data
            user_data = {
                "username": "existinguser",
                "email": "new@example.com",
                "password": "password123",
                "is_photographer": False,
                "is_admin": False
            }
            user_in = UserCreate(**user_data)
            
            # Mock email already exists
            mock_crud.get_user_by_username.return_value = MagicMock()
            
            # Call the endpoint and expect exception
            with pytest.raises(HTTPException) as excinfo:
                router.routes[0].endpoint(
                    user_in=user_in,
                    db=mock_db
                )
            
            # Verify exception
            assert excinfo.value.status_code == 400
            assert excinfo.value.detail == "Username already registered"
            
            # Verify create_user not called
            mock_crud.get_user_by_username.assert_called_once_with(mock_db, user_in.username)
            assert not mock_crud.create_user.called
        
        @patch("app.routers.auth.crud")
        def test_register_user_email_exists(self, mock_crud, mock_db):
            """Test registration with existing email"""
            # Setup test data
            user_data = {
                "username": "existinguser",
                "email": "existing@example.com",
                "password": "password123",
                "is_photographer": False,
                "is_admin": False
            }
            user_in = UserCreate(**user_data)
            
            # Mock email already exists
            mock_crud.get_user_by_email.return_value = MagicMock()
            
            # Call the endpoint and expect exception
            with pytest.raises(HTTPException) as excinfo:
                router.routes[0].endpoint(
                    user_in=user_in,
                    db=mock_db
                )
            
            # Verify exception
            assert excinfo.value.status_code == 400
            assert excinfo.value.detail == "Email already registered"
            
            # Verify create_user not called
            mock_crud.get_user_by_email.assert_called_once_with(mock_db, user_in.email)
            assert not mock_crud.create_user.called

    @patch("app.routers.auth.verify_password")
    @patch("app.routers.auth.create_access_token")
    @patch("app.routers.auth.crud")
    def test_login_success(self, mock_crud, mock_create_token, mock_verify_password, mock_db):
        """Test successful login"""
        # Setup test data
        form_data = OAuth2PasswordRequestForm(
            username="user@example.com",
            password="password123",
            scope=""
        )
        mock_user = MagicMock(id=1)
        mock_response = MagicMock(spec=Response)
        
        # Configure mocks
        mock_crud.get_user_by_email.return_value = mock_user
        mock_verify_password.return_value = True
        mock_create_token.return_value = "mock_access_token"
        
        # Call the endpoint
        result = router.routes[1].endpoint(
            response=mock_response,
            form_data=form_data,
            db=mock_db
        )