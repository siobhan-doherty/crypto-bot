"""Unit tests for API MongoDB operations."""
import pytest
from unittest.mock import MagicMock, patch
from src.api_user.database.mongo import MongoDB


@pytest.fixture
def mock_mongo():
    with patch('src.api_user.database.mongo.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        yield mock_client


def test_mongo_connection(mock_mongo):
    """Test MongoDB connection."""
    db = MongoDB("mongodb://test:27017")
    assert db.client is not None
    mock_mongo.assert_called_once()


def test_mongo_get_collection(mock_mongo):
    """Test getting a collection."""
    db = MongoDB("mongodb://test:27017")
    collection = db.get_collection("test_db", "test_collection")
    assert collection is not None
