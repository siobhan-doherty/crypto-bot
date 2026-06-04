from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from api_user.services.market_service import MarketService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return MarketService(mock_repo)


def test_get_date_range_uses_fallback(mock_repo, service):
    mock_repo.get_date_range.return_value = (None, None)
    result = service.get_date_range()
    assert "min_date" in result
    assert "max_date" in result
    # should be within last 7 days
    max_date = datetime.fromisoformat(result["max_date"])
    min_date = datetime.fromisoformat(result["min_date"])
    assert (max_date - min_date).days == 7


def test_get_date_range_from_repo(mock_repo, service):
    mock_repo.get_date_range.return_value = (1000, 2000)
    result = service.get_date_range()
    min_date = datetime.fromtimestamp(1000 / 1000, tz=timezone.utc)
    max_date = datetime.fromtimestamp(2000 / 1000, tz=timezone.utc)
    assert result["min_date"] == min_date.isoformat()
    assert result["max_date"] == max_date.isoformat()


def test_get_ohlcv_converts_data(mock_repo, service):
    mock_repo.get_ohlcv.return_value = [
        {
            "_id": "abc",
            "symbol": "BTCUSDT",
            "open_time": 1000,
            "close_time": 1015,
            "open": 50000,
            "high": 51000,
            "low": 49000,
            "close": 50500,
            "volume": 100,
        }
    ]
    result = service.get_ohlcv(symbol="BTCUSDT", interval="15m")
    assert len(result) == 1
    assert result[0]["symbol"] == "BTCUSDT"
    assert result[0]["open_datetime"] is not None
    assert result[0]["interval"] == "15m"
