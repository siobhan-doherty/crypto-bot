"""Unit tests for PriceAlertEngine."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, Mock
from src.alerts.price_alert import PriceAlertEngine
from src.alerts.models import PriceAlert

@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.telegram_bot_token = "test_token"
    settings.telegram_chat_id = "test_chat_id"
    settings.sentiment_provider = "mistral"
    settings.mistral_api_key = "test_api_key"
    settings.mistral_model = "test_model"
    settings.hf_token = "test_hf_token"
    settings.hf_model = "test_hf_model"
    settings.enable_sentiment_fallback = True
    settings.check_interval_seconds = 60
    settings.default_fallback_exchanges = ["binance", "kraken"]
    settings.mongo_uri = "mongodb://test:27017"
    settings.sentiment_retention_seconds = 31536000
    settings.alerts = [
        {"symbol": "BTC/USDT", "exchange": "binance", "threshold": 70000.0, "condition": "above"},
        {"symbol": "ETH/USDT", "exchange": "binance", "threshold": 4000.0, "condition": "above"},
    ]
    return settings

@pytest.fixture
def mock_get_price():
    """Mock get_price to return fixed values for testing."""
    with patch('src.alerts.price_alert.get_price') as mock:
        def get_price_mock(symbol, exchange=None, fallback_exchanges=None):
            prices = {
                "BTC/USDT": 65000.0,
                "ETH/USDT": 2000.0,
            }
            return prices.get(symbol, 0.0)
        mock.side_effect = get_price_mock
        yield mock


@pytest.fixture
def engine(mock_settings, mock_get_price):
    """Create PriceAlertEngine with mocked dependencies."""
    with patch('src.alerts.price_alert.TelegramNotifier') as mock_notifier:
        with patch('src.alerts.price_alert.get_sentiment_provider') as mock_sentiment:
            with patch('src.alerts.price_alert.HuggingFaceSentiment') as mock_hf:
                with patch('src.alerts.price_alert.SentimentRepository') as mock_repo:
                    with patch('src.alerts.price_alert.PatternDetector') as mock_pattern:
                        return PriceAlertEngine(mock_settings)

def test_init(engine):
    """Test engine initialization."""
    assert len(engine.alerts) == 2
    assert engine.alerts[0].symbol == "BTC/USDT"
    assert engine.alerts[1].symbol == "ETH/USDT"

def test_fetch_prices(engine):
    """Test fetching prices for all alerts."""
    prices = engine.fetch_prices()
    assert "binance:BTC/USDT" in prices
    assert "binance:ETH/USDT" in prices
    assert prices["binance:BTC/USDT"] == 65000.0
    assert prices["binance:ETH/USDT"] == 2000.0

def test_check_alerts_above(engine):
    """Test alert triggering when price is above threshold."""
    prices = {"binance:BTC/USDT": 75000.0}
    messages = engine.check_alerts(prices)
    assert len(messages) == 1
    assert "above" in messages[0]
    assert "$75,000.00" in messages[0]

def test_check_alerts_below(engine):
    """Test alert triggering when price is below threshold."""
    engine.alerts[0].threshold = 60000.0
    engine.alerts[0].condition = "below"
    prices = {"binance:BTC/USDT": 55000.0}
    messages = engine.check_alerts(prices)
    assert len(messages) == 1
    assert "below" in messages[0]

def test_check_alerts_no_trigger(engine):
    """Test no alerts triggered when price is within range."""
    prices = {"binance:BTC/USDT": 65000.0}  # Below 70000 threshold
    messages = engine.check_alerts(prices)
    assert len(messages) == 0

def test_check_alerts_cooldown(engine):
    """Test alert cooldown prevents duplicate alerts."""
    prices = {"binance:BTC/USDT": 75000.0}
    # First trigger
    messages1 = engine.check_alerts(prices)
    assert len(messages1) == 1

    # Second trigger within cooldown period (1 hour)
    messages2 = engine.check_alerts(prices)
    assert len(messages2) == 0  # Cooldown prevents duplicate

def test_enhance_message_with_sentiment(engine):
    """Test sentiment enhancement with storage."""
    with patch.object(engine.sentiment, 'classify') as mock_classify:
        mock_classify.return_value = {
            "labels": ["bullish"],
            "scores": [0.85],
            "usage": {}
        }
        with patch.object(engine.sentiment_repo, 'store_sentiment') as mock_store:
            message = "Test alert message"
            enhanced, sentiment_result = engine.enhance_message_with_sentiment(
                message, "BTC/USDT", 65000.0, "binance"
            )
            assert sentiment_result is not None
            assert sentiment_result.top_label == "bullish"
            assert "Sentiment (mistral)" in enhanced
            mock_store.assert_called_once()
            mock_classify.assert_called_once()

def test_track_cost(engine):
    """Test cost tracking."""
    engine._track_cost("mistral", "test message", success=True)
    assert engine.cost_tracker["mistral"]["requests"] == 1
    assert engine.cost_tracker["mistral"]["tokens"] > 0
    assert engine.cost_tracker["mistral"]["cost"] >= 0

def test_get_price_history(engine):
    """Test fetching price history."""
    with patch('ccxt.binance') as mock_exchange:
        mock_exchange.return_value.fetch_ohlcv.return_value = [
            [1609459200000, 64000.0, 64100.0, 63900.0, 64050.0, 100.0],
            [1609459260000, 64050.0, 64150.0, 64000.0, 64100.0, 120.0],
        ]
        df = engine._get_price_history("BTC/USDT", limit=2)
        assert df is not None
        assert len(df) == 2
        assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
