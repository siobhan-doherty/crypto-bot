from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the src directory to the Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "src"))

from api_user.main import app

# Test client
client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct welcome message and docs links"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "redoc" in data


class TestMarketEndpoints:
    """Test suite for market-related endpoints"""

    @patch("api_user.router.get_mongo_client")
    def test_get_ohlcv(self, mock_mongo):
        """Test the /api/market/ohlcv endpoint"""

        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo.return_value = MagicMock(__getitem__=lambda *args: mock_db)
        mock_db.__getitem__.return_value = mock_collection

        test_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
        mock_collection.find.return_value.sort.return_value.limit.return_value = [
            {
                "timestamp": test_time,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
                "symbol": "BTCUSDT",
                "interval": "15m",
            }
        ]

        # Test with required parameters
        response = client.get("/api/market/ohlcv?symbol=BTCUSDT")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "timestamp" in data[0]
            assert "open" in data[0]
            assert "high" in data[0]
            assert "low" in data[0]
            assert "close" in data[0]
            assert "volume" in data[0]
            assert "symbol" in data[0]
            assert "interval" in data[0]

    @patch("api_user.router.get_mongo_client")
    def test_get_date_range(self, mock_mongo):
        """Test the /api/market/date_range endpoint"""

        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo.return_value = MagicMock(__getitem__=lambda *args: mock_db)
        mock_db.__getitem__.return_value = mock_collection

        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        mock_collection.find_one.side_effect = [
            {"timestamp": week_ago},
            {"timestamp": now},
        ]

        response = client.get("/api/market/range")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "min_date" in data
        assert "max_date" in data
        assert data["min_date"] <= data["max_date"]


def test_invalid_endpoint():
    """Test that invalid endpoints return 404"""
    response = client.get("/nonexistent/endpoint")
    assert response.status_code == status.HTTP_404_NOT_FOUND
