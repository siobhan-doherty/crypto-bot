from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from api_user import dependencies   # noqa: E402
from api_user.main import app   # noqa: E402


def build_mock_db_with_collection() -> tuple[MagicMock, MagicMock, MagicMock]:
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()

    mock_client.__getitem__.return_value = mock_db
    mock_client.cryptobot = mock_db
    mock_db.__getitem__.return_value = mock_collection

    return mock_client, mock_db, mock_collection


@pytest.fixture(scope="session")
def mock_dependency_mongo_client():
    """
    Patch dependency-layer reference used by app, not just original
    mongo module symbol.
    """
    with patch("api_user.dependencies.get_mongo_client") as mock:
        yield mock


@pytest.fixture(scope="session")
def client(mock_dependency_mongo_client):
    mock_dependency_mongo_client.return_value = MagicMock()
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_singleton():
    dependencies._client = None
    yield
    dependencies._client = None


@pytest.fixture(autouse=True)
def reset_mock(mock_dependency_mongo_client):
    mock_dependency_mongo_client.reset_mock()
    yield


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": "Welcome to the Crypto Dashboard API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


def test_invalid_endpoint(client):
    response = client.get("/nonexistent/endpoint")
    assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMarketEndpoints:
    def test_get_ohlcv_filters_by_symbol(self, client, mock_dependency_mongo_client):
        mock_client, _, mock_collection = build_mock_db_with_collection()
        mock_dependency_mongo_client.return_value = mock_client

        open_time = int(
            datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc).timestamp() * 1000
        )
        close_time = int(
            datetime(2023, 1, 1, 0, 15, tzinfo=timezone.utc).timestamp() * 1000
        )

        mock_find = MagicMock()
        mock_collection.find.return_value = mock_find
        mock_find.sort.return_value = [
            {
                "_id": "abc123",
                "symbol": "BTCUSDT",
                "interval": "15m",
                "open_time": open_time,
                "close_time": close_time,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
                "quote_volume": 5000.0,
                "num_trades": 10,
                "taker_base_volume": 400.0,
                "taker_quote_volume": 2000.0,
            }
        ]

        response = client.get("/api/market/ohlcv?symbol=BTCUSDT")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 1
        assert data[0]["symbol"] == "BTCUSDT"
        assert data[0]["interval"] == "15m"
        assert data[0]["open"] == 100.0
        assert data[0]["high"] == 101.0
        assert data[0]["low"] == 99.0
        assert data[0]["close"] == 100.5
        assert data[0]["volume"] == 1000.0

        mock_collection.find.assert_called_once_with({"symbol": "BTCUSDT"})

    def test_get_ohlcv_with_limit_returns_chronological_order(
        self, client, mock_dependency_mongo_client
    ):
        mock_client, _, mock_collection = build_mock_db_with_collection()
        mock_dependency_mongo_client.return_value = mock_client

        newer_open = int(
            datetime(2023, 1, 1, 0, 15, tzinfo=timezone.utc).timestamp() * 1000
        )
        older_open = int(
            datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc).timestamp() * 1000
        )

        mock_find = MagicMock()
        mock_sort = MagicMock()
        mock_collection.find.return_value = mock_find
        mock_find.sort.return_value = mock_sort
        mock_sort.limit.return_value = [
            {
                "_id": "newer",
                "symbol": "BTCUSDT",
                "interval": "15m",
                "open_time": newer_open,
                "close_time": newer_open + 900_000,
                "open": 110.0,
                "high": 111.0,
                "low": 109.0,
                "close": 110.5,
                "volume": 900.0,
            },
            {
                "_id": "older",
                "symbol": "BTCUSDT",
                "interval": "15m",
                "open_time": older_open,
                "close_time": older_open + 900_000,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
            },
        ]

        response = client.get("/api/market/ohlcv?symbol=BTCUSDT&limit=2")

        assert response.status_code == status.HTTP_200_OK
        assert [item["_id"] for item in response.json()] == ["older", "newer"]

    def test_get_date_range(self, client, mock_dependency_mongo_client):
        mock_client, _, mock_collection = build_mock_db_with_collection()
        mock_dependency_mongo_client.return_value = mock_client

        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        mock_collection.aggregate.return_value = [
            {
                "_id": None,
                "min_time": int(week_ago.timestamp() * 1000),
                "max_time": int(now.timestamp() * 1000),
            }
        ]

        response = client.get("/api/market/range")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "min_date" in data
        assert "max_date" in data
        assert data["min_date"] <= data["max_date"]
