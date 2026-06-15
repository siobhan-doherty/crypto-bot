from unittest.mock import patch, MagicMock


def test_health_endpoint():
    # patch get_mongo_client function inside health router module
    with patch("api_user.routes.health.get_mongo_client") as mock_get_client:
        # create mock MongoDB client with required server_info method
        mock_client = MagicMock()
        mock_client.server_info.return_value = {"ok": 1}
        mock_get_client.return_value = mock_client

        # import TestClient & app inside patch context
        from fastapi.testclient import TestClient
        from api_user.main import app

        client = TestClient(app)
        response = client.get("/api/health")

        # adjust assertion to match actual success response
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "database": "connected"}
