"""
FastAPI testing using httpx.AsyncClient with direct patching of get_mongo_client.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import mongomock
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import api_user.dependencies as deps
import api_user.routes.health as health_routes
from api_user.main import app


@pytest_asyncio.fixture
async def client():
    deps._client = None
    app.dependency_overrides.clear()
    async with AsyncClient(
        transport = ASGITransport(app = app), 
        base_url = "http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()
    deps._client = None


def create_mock_client_with_data():
    client = mongomock.MongoClient()
    client.server_info = MagicMock(return_value = {"ok": 1})
    return client, client.cryptobot, client.cryptobot.historical_data_15m


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Crypto Dashboard API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    mock_client, _, _ = create_mock_client_with_data()
    with patch.object(health_routes, "get_mongo_client", return_value = mock_client):
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


@pytest.mark.asyncio
async def test_invalid_endpoint(client: AsyncClient):
    response = await client.get("/nonexistent/endpoint")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_ohlcv_filters_by_symbol(client: AsyncClient):
    mock_client, _, collection = create_mock_client_with_data()
    open_time = int(datetime(2023, 1, 1, 0, 0, tzinfo = timezone.utc).timestamp() * 1000)
    close_time = int(datetime(2023, 1, 1, 0, 15, tzinfo = timezone.utc).timestamp() * 1000)

    collection.insert_one(
        {
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
    )

    app.dependency_overrides[deps.get_db_client] = lambda: mock_client
    response = await client.get("/api/market/ohlcv?symbol=BTCUSDT")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "BTCUSDT"
    assert data[0]["open"] == 100.0


@pytest.mark.asyncio
async def test_get_date_range(client: AsyncClient):
    mock_client, _, collection = create_mock_client_with_data()
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days = 7)

    collection.insert_one({"open_time": int(week_ago.timestamp() * 1000)})
    collection.insert_one({"open_time": int(now.timestamp() * 1000)})

    app.dependency_overrides[deps.get_db_client] = lambda: mock_client
    response = await client.get("/api/market/range")

    assert response.status_code == 200
    data = response.json()
    assert "min_date" in data
    assert "max_date" in data
    assert data["min_date"] <= data["max_date"]
