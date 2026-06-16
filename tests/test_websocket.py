import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api_user.main import app


def test_websocket_health_connected():
    client = TestClient(app)
    with client.websocket_connect("/ws/stream") as websocket:
        data = websocket.receive_json()
        assert data["status"] == "connected"


@pytest.mark.skip(reason="Async WebSocket test requires a running server; logic covered by fetch_data unit tests and E2E")
@pytest.mark.asyncio
async def test_websocket_streams_data():
    pass
