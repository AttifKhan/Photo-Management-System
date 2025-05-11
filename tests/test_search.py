import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.routers.search import search_photos
from app.schemas.search import SearchResult
from app.schemas.photo import PhotoOut

class TestSearchRoutes:
    # @pytest.mark.asyncio
    # async def test_search_photos_success(self, mock_db, mock_current_user):
    #     # Arrange
    #     query = "nature"
    #     skip = 0
    #     limit = 20
        
    #     # Create mock photos
    #     mock_photo1 = MagicMock(id=1, user_id=1, filename="test1.jpg", caption="Test 1")
    #     mock_photo2 = MagicMock(id=2, user_id=2, filename="test2.jpg", caption="Test 2")
    #     mock_photos = [mock_photo1, mock_photo2]
        
    #     # Mock the PhotoOut.from_orm method
    #     photo_out1 = PhotoOut.from_orm(mock_photo1)
    #     photo_out2 = PhotoOut.from_orm(mock_photo2)
    #     expected_items = [photo_out1, photo_out2]
        
    #     # Mock crud method
    #     with patch("app.db.crud.search_photos_by_tag", return_value=mock_photos), \
    #          patch("app.schemas.photo.PhotoOut.from_orm", side_effect=[photo_out1, photo_out2]):
            
    #         # Act
    #         result = await search_photos(query, skip, limit, mock_db, mock_current_user)
            
    #         # Assert
    #         assert isinstance(result, SearchResult)
    #         assert result.items == expected_items
    #         assert result.skip == skip
    #         assert result.limit == limit
    
    @pytest.mark.asyncio
    async def test_search_photos_empty_result(self, mock_db, mock_current_user):
        # Arrange
        query = "nonexistent"
        skip = 0
        limit = 20
        
        # Mock crud method to return empty list
        with patch("app.db.crud.search_photos_by_tag", return_value=[]):
            
            # Act
            result = await search_photos(query, skip, limit, mock_db, mock_current_user)
            
            # Assert
            assert isinstance(result, SearchResult)
            assert result.items == []
            assert result.skip == skip
            assert result.limit == limit
    
    # @pytest.mark.asyncio
    # async def test_search_photos_pagination(self, mock_db, mock_current_user):
    #     # Arrange
    #     query = "nature"
    #     skip = 5
    #     limit = 10
        
    #     # Create mock photos
    #     mock_photo1 = MagicMock(id=6, user_id=1, filename="test6.jpg", caption="Test 6")
    #     mock_photo2 = MagicMock(id=7, user_id=2, filename="test7.jpg", caption="Test 7")
    #     mock_photos = [mock_photo1, mock_photo2]
        
    #     # Mock the PhotoOut.from_orm method
    #     photo_out1 = PhotoOut.from_orm(mock_photo1)
    #     photo_out2 = PhotoOut.from_orm(mock_photo2)
    #     expected_items = [photo_out1, photo_out2]
        
    #     # Mock crud method
    #     with patch("app.db.crud.search_photos_by_tag", return_value=mock_photos), \
    #          patch("app.schemas.photo.PhotoOut.from_orm", side_effect=[photo_out1, photo_out2]):
            
    #         # Act
    #         result = await search_photos(query, skip, limit, mock_db, mock_current_user)
            
    #         # Assert
    #         assert isinstance(result, SearchResult)
    #         assert result.items == expected_items
    #         assert result.skip == skip
    #         assert result.limit == limit
            
    #         # Verify the crud method was called with correct parameters
    #         # (This would normally be done using mock assertions)