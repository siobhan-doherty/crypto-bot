import pytest
from mongomock import MongoClient

from api_user.repositories.market_repo import MarketRepository


@pytest.fixture
def repo():
    client = MongoClient()
    db = client.cryptobot
    # initial sample historical data
    db.historical_data_15m.insert_many(
        [
            {
                "symbol": "BTCUSDT",
                "open_time": 1000,
                "close_time": 1015,
                "open": 50000,
                "high": 51000,
                "low": 49000,
                "close": 50500,
                "volume": 100,
            },
            {
                "symbol": "BTCUSDT",
                "open_time": 1015,
                "close_time": 1030,
                "open": 50500,
                "high": 51500,
                "low": 49500,
                "close": 51000,
                "volume": 150,
            },
            {
                "symbol": "ETHUSDT",
                "open_time": 1000,
                "close_time": 1015,
                "open": 3000,
                "high": 3100,
                "low": 2900,
                "close": 3050,
                "volume": 500,
            },
        ]
    )
    return MarketRepository(client)


def test_get_date_range(repo):
    min_time, max_time = repo.get_date_range()
    assert min_time == 1000
    assert max_time == 1015


def test_get_ohlcv_no_filters(repo):
    data = repo.get_ohlcv()
    assert len(data) == 3
    assert data[0]["symbol"] == "ETHUSDT"


def test_get_ohlcv_filter_symbol(repo):
    data = repo.get_ohlcv(symbol="BTCUSDT")
    assert len(data) == 2
    assert all(d["symbol"] == "BTCUSDT" for d in data)


def test_get_ohlcv_filter_time_range(repo):
    data = repo.get_ohlcv(start_time=1000, end_time=1015)
    assert len(data) == 3
    for d in data:
        assert 1000 <= d["open_time"] <= 1015


def test_get_ohlcv_limit(repo):
    data = repo.get_ohlcv(limit=1)
    assert len(data) == 1
