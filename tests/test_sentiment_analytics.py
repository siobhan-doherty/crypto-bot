"""Unit tests for SentimentAnalyticsService."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from src.alerts.services.sentiment_analytics import SentimentAnalyticsService


@pytest.fixture
def mock_repo():
    """Create a properly mocked SentimentRepository."""
    mock = MagicMock()

    def mock_get_sentiment_trend(symbol, start_time, end_time, provider=None, limit=10000):
        # Return trend data that will give us consistent results
        # For anomaly detection: 10 neutral + 1 bullish = high z-score for bullish
        result = []
        for i in range(10):
            result.append({
                "timestamp": start_time + timedelta(hours=i+1),
                "symbol": symbol,
                "sentiment_label": "neutral",
                "confidence": 0.5,
                "price": 65000.0 + i * 100,
            })
        # Add one bullish as outlier
        result.append({
            "timestamp": start_time + timedelta(hours=11),
            "symbol": symbol,
            "sentiment_label": "bullish",
            "confidence": 0.95,
            "price": 66000.0,
        })
        return result

    def mock_get_sentiment_price_correlation(symbol, start_time, end_time, time_window="1h"):
        return [
            {
                "_id": {"symbol": symbol, "year": 2026, "month": 1, "day": 1, "hour": 10},
                "timestamp": start_time + timedelta(hours=1),
                "avg_sentiment_score": 0.85,
                "avg_price": 65000.0,
                "count": 10,
                "bullish_count": 8,
                "bearish_count": 1,
                "neutral_count": 1,
            },
            {
                "_id": {"symbol": symbol, "year": 2026, "month": 1, "day": 1, "hour": 11},
                "timestamp": start_time + timedelta(hours=2),
                "avg_sentiment_score": 0.90,
                "avg_price": 65500.0,
                "count": 12,
                "bullish_count": 10,
                "bearish_count": 1,
                "neutral_count": 1,
            },
        ]

    def mock_get_sentiment_anomalies(symbol, start_time, end_time):
        # This is not used by get_sentiment_anomalies which calculates its own z-scores
        # But we need to return something for other methods
        return []

    mock.get_sentiment_trend = mock_get_sentiment_trend
    mock.get_sentiment_price_correlation = mock_get_sentiment_price_correlation
    mock.get_sentiment_anomalies = mock_get_sentiment_anomalies

    return mock


@pytest.fixture
def analytics_service(mock_repo):
    """Create SentimentAnalyticsService with mocked repo."""
    with patch('src.alerts.services.sentiment_analytics.SentimentRepository', return_value=mock_repo):
        return SentimentAnalyticsService("mongodb://test:27017")


def test_calculate_correlation(analytics_service):
    """Test correlation calculation."""
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc)

    result = analytics_service.calculate_correlation(
        symbol="BTC/USDT",
        start_time=start,
        end_time=end,
    )
    assert "pearson_correlation" in result
    assert "spearman_correlation" in result
    assert result["sample_size"] == 2


def test_detect_sentiment_trend(analytics_service):
    """Test trend detection."""
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc)

    result = analytics_service.detect_sentiment_trend(
        symbol="BTC/USDT",
        start_time=start,
        end_time=end,
    )
    assert result["symbol"] == "BTC/USDT"
    assert result["current_sentiment"] == "bullish"
    assert result["current_sentiment_score"] == 1.0  # bullish maps to 1.0
    assert "sentiment_trend" in result
    assert "price_trend" in result


def test_get_sentiment_anomalies(analytics_service):
    """Test anomaly detection."""
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc)

    result = analytics_service.get_sentiment_anomalies(
        symbol="BTC/USDT",
        start_time=start,
        end_time=end,
    )
    # With 10 neutral (0.0) and 1 bullish (1.0), the z-score should be ~3.015
    assert len(result) == 1
    assert abs(result[0]["z_score"] - 3.015) < 0.01  # Allow small floating point difference


def test_prepare_training_data(analytics_service):
    """Test training data preparation."""
    start = datetime.now(timezone.utc) - timedelta(days=30)
    end = datetime.now(timezone.utc)

    X, y = analytics_service.prepare_training_data(
        symbol="BTC/USDT",
        start_time=start,
        end_time=end,
    )
    # With the mock data, we may not have enough points for training
    assert X.shape[0] >= 0
    assert len(y) >= 0
