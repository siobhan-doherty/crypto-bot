"""Unit tests for SentimentRepository with proper mocking."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from src.alerts.repositories.sentiment_repository import SentimentRepository


@pytest.fixture
def mock_mongo_client():
    """Create a mock MongoDB client."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    mock_db.list_collection_names.return_value = []
    mock_db.create_collection.return_value = mock_collection
    mock_collection.create_indexes.return_value = None
    mock_client.server_selection_timeout = 5000
    return mock_client, mock_db, mock_collection


@pytest.fixture
def mock_repo():
    """Create SentimentRepository with mocked MongoDB."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    # configure mock client to return mock db and collection
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    mock_db.list_collection_names.return_value = []
    mock_db.create_collection.return_value = mock_collection
    mock_collection.create_indexes.return_value = None
    mock_collection.estimated_document_count.return_value = 1000
    mock_collection.database = mock_db
    mock_collection.insert_one.return_value = MagicMock(inserted_id = "test_id_123")
    mock_collection.insert_many.return_value = MagicMock(inserted_ids = ["id1", "id2", "id3"])
    mock_collection.find.return_value = MagicMock(__iter__=MagicMock(return_value = []))
    mock_collection.aggregate.return_value = []
    
    # create a mock for _get_client that returns our mock_client
    def mock_get_client():
        return mock_client
    
    with patch('src.alerts.repositories.sentiment_repository.MongoClient', return_value = mock_client):
        repo = SentimentRepository("mongodb://test:27017")
        # override _get_client method to return our mock client
        repo._get_client = mock_get_client
        # override the internal collection reference to use our mock
        repo._collection = mock_collection
        return repo, mock_collection


def test_store_sentiment(mock_repo):
    """Test storing a single sentiment record."""
    repo, mock_collection = mock_repo
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "test_id_123"
    mock_collection.insert_one.return_value = mock_insert_result
    
    timestamp = datetime.now(timezone.utc)
    result = repo.store_sentiment(
        symbol = "BTC/USDT",
        sentiment_label = "bullish",
        confidence = 0.95,
        text = "Test message",
        provider = "mistral",
        price = 70000.0,
        exchange = "binance",
        timestamp = timestamp,
        additional_metadata = {"test": "value"}
    )
    
    assert result == "test_id_123"
    mock_collection.insert_one.assert_called_once()
    call_args = mock_collection.insert_one.call_args[0][0]
    assert call_args["symbol"] == "BTC/USDT"
    assert call_args["sentiment_label"] == "bullish"
    assert call_args["confidence"] == 0.95
    assert call_args["provider"] == "mistral"
    assert call_args["metadata"]["test"] == "value"


def test_store_batch(mock_repo):
    """Test storing multiple sentiment records."""
    repo, mock_collection = mock_repo
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_ids = ["id1", "id2", "id3"]
    mock_collection.insert_many.return_value = mock_insert_result
    
    records = [
        {
            "timestamp": datetime.now(timezone.utc),
            "symbol": "BTC/USDT",
            "sentiment_label": "bullish",
            "confidence": 0.95,
            "text": "Test 1",
            "provider": "mistral",
            "price": 70000.0,
            "exchange": "binance",
            "metadata": {}
        },
        {
            "timestamp": datetime.now(timezone.utc),
            "symbol": "ETH/USDT",
            "sentiment_label": "bearish",
            "confidence": 0.85,
            "text": "Test 2",
            "provider": "huggingface",
            "price": 4000.0,
            "exchange": "kraken",
            "metadata": {}
        }
    ]
    result = repo.store_batch(records)
    assert result == ["id1", "id2", "id3"]
    mock_collection.insert_many.assert_called_once_with(records)


def test_get_collection_stats(mock_repo):
    """Test getting collection statistics."""
    repo, mock_collection = mock_repo
    mock_collection.estimated_document_count.return_value = 1000
    mock_collection.database.command.return_value = {"size": 1024000, "avgObjSize": 1024}
    mock_collection.database.__getitem__.return_value = mock_collection
    stats = repo.get_collection_stats()
    assert stats["count"] == 1000
    assert stats["size"] == 1024000
    assert stats["avg_obj_size"] == 1024


def test_get_sentiment_trend():
    """Test retrieving sentiment trend data."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    start_time = datetime.now(timezone.utc) - timedelta(days = 1)
    end_time = datetime.now(timezone.utc)
    
    # create mock cursor with proper pymongo-style chainable methods
    expected_results = [
        {"timestamp": start_time, "symbol": "BTC/USDT", "sentiment_label": "bullish", "confidence": 0.95},
        {"timestamp": end_time, "symbol": "BTC/USDT", "sentiment_label": "neutral", "confidence": 0.70},
    ]
    mock_cursor = MagicMock()
    mock_cursor.__iter__ = MagicMock(return_value = iter(expected_results))
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_collection.find.return_value = mock_cursor
    
    def mock_get_client():
        return mock_client
    
    with patch('src.alerts.repositories.sentiment_repository.MongoClient', return_value = mock_client):
        repo = SentimentRepository("mongodb://test:27017")
        repo._get_client = mock_get_client
        repo._collection = mock_collection
        
        result = repo.get_sentiment_trend("BTC/USDT", start_time, end_time)
        assert len(result) == 2
        assert result[0]["symbol"] == "BTC/USDT"
        assert result[1]["sentiment_label"] == "neutral"


def test_get_sentiment_price_correlation(mock_repo):
    """Test retrieving sentiment-price correlation data."""
    repo, mock_collection = mock_repo
    start_time = datetime.now(timezone.utc) - timedelta(days = 1)
    end_time = datetime.now(timezone.utc)
    
    mock_aggregate_result = [
        {
            "_id": {"symbol": "BTC/USDT", "year": 2026, "month": 1, "day": 29, "hour": 10},
            "timestamp": start_time + timedelta(hours = 1),
            "avg_sentiment_score": 0.85,
            "avg_price": 70000.0,
            "count": 10,
            "bullish_count": 8,
            "bearish_count": 1,
            "neutral_count": 1,
        }
    ]
    mock_collection.aggregate.return_value = mock_aggregate_result
    
    result = repo.get_sentiment_price_correlation("BTC/USDT", start_time, end_time, "1h")
    assert len(result) == 1
    assert result[0]["avg_sentiment_score"] == 0.85
    assert result[0]["avg_price"] == 70000.0


def test_get_aggregated_sentiment(mock_repo):
    """Test getting aggregated sentiment statistics."""
    repo, mock_collection = mock_repo
    start_time = datetime.now(timezone.utc) - timedelta(days = 1)
    end_time = datetime.now(timezone.utc)
    
    mock_aggregate_result = [
        {
            "_id": {"year": 2026, "month": 1, "day": 29, "hour": 10},
            "count": 10,
            "avg_confidence": 0.85,
            "bullish": 8,
            "bearish": 1,
            "neutral": 1,
        }
    ]
    mock_collection.aggregate.return_value = mock_aggregate_result
    
    result = repo.get_aggregated_sentiment(start_time, end_time, "hour")
    assert len(result) == 1
    assert result[0]["count"] == 10
    assert result[0]["avg_confidence"] == 0.85
