import asyncio
import pytest
import websockets
from fastapi.testclient import TestClient
from api_user.main import app


def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/ws/stream") as websocket:
        data = websocket.receive_json()
        assert data["status"] == "connected"
