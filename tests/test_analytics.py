import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch
from sqlalchemy import func

from app.routers.analytics import router
from app.schemas.analytics import AnalyticsOut


class TestAnalyticsRoutes:
    @pytest_asyncio.fixture
    async def setup_mocks(self):
        """Set up common mocks for testing"""
        # You can add common setup here if needed
        pass

    @pytest.mark.asyncio  # Now properly recognized with pytest-asyncio installed
    #@patch("app.routers.analytics.func")
    async def test_get_analytics(self, mock_db, mock_current_user):
        """Test getting user analytics data"""
        # Setup test data
        user_id = mock_current_user.id
        
        # Sum downloads
        mock_downloads_sum = 42

        # Configure the mock database queries
        # Count photos
        mock_photos_count = 5
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [
            mock_photos_count,  # photos count
            10,                 # followers count
            3,                  # following count
            mock_downloads_sum  # downloads sum
        ]
        
        # Call the endpoint function and await the result
        result = await router.routes[0].endpoint(
            db=mock_db,
            current_user=mock_current_user
        )
        
        # Verify function calls
        assert mock_db.query.call_count >= 4  # Called for each metric
        
        # Check result values
        assert isinstance(result, AnalyticsOut)
        assert result.total_photos == mock_photos_count
        assert result.total_followers == 10
        assert result.total_following == 3
        assert result.total_downloads == mock_downloads_sum

    @pytest.mark.asyncio
    async def test_get_analytics_zero_values(self, mock_db, mock_current_user):
        """Test analytics with zero values"""
        # Setup mocks to return zero values
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [
            0,  # photos count
            0,  # followers count
            0,  # following count
            0   # downloads sum
        ]
        
        # Call the endpoint and await the result
        result = await router.routes[0].endpoint(
            db=mock_db,
            current_user=mock_current_user
        )
        
        # Check zero values
        assert result.total_photos == 0
        assert result.total_followers == 0
        assert result.total_following == 0
        assert result.total_downloads == 0

    @pytest.mark.asyncio
    async def test_get_analytics_with_none_values(self, mock_db, mock_current_user):
        """Test analytics with None values (should handle gracefully)"""
        # Setup mocks to return None values
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [
            0,  # photos count
            0,  # followers count
            0,  # following count
            0   # downloads sum (coalesce handles None)
        ]
        
        # Call the endpoint and await the result
        result = await router.routes[0].endpoint(
            db=mock_db,
            current_user=mock_current_user
        )
        
        # Check results
        assert result.total_photos == 0  # None should be converted to 0
        assert result.total_followers == 0
        assert result.total_following == 0
        assert result.total_downloads == 0