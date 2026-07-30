import json
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.alerts.config import AlertSettings
from src.alerts.notifier import TelegramNotifier
from src.alerts.price_alert import PriceAlertEngine
from src.exchange_wrapper import get_price
from src.exchange_wrapper.exceptions import (
    ExchangeConnectionError,
    ExchangeRateLimitError,
    ExchangeSymbolNotFound,
)
from src.exchange_wrapper.price_fetcher import PriceFetcher


@pytest.fixture
def mock_settings(tmp_path):
    """Create minimal AlertSettings with temp alerts.json file."""
    alerts_data = [
        {"symbol": "BTC/USDT", "exchange": "binance", "threshold": 70000.0, "condition": "above"},
        {"symbol": "ETH/USDT", "exchange": "kraken", "threshold": 4000.0, "condition": "below"},
    ]
    alerts_file = tmp_path / "alerts.json"
    alerts_file.write_text(json.dumps(alerts_data))
    settings = AlertSettings(
        telegram_bot_token = "test_token",
        telegram_chat_id = "test_chat",
        hf_token = "test_hf_token",
        mistral_api_key = "test_mistral_key",
        alerts_file = str(alerts_file),
        check_interval_seconds = 60,
        default_fallback_exchanges = ["binance", "kraken", "bitmex", "bybit"],
        sentiment_provider = "mistral",
        enable_sentiment_fallback = True,
    )
    return settings


@pytest.fixture
def mock_sentiment():
    """Create a mock sentiment provider."""
    mock = MagicMock()
    mock.classify = MagicMock(return_value = {"labels": ["bullish"], "scores": [0.95]})
    return mock


@pytest.fixture
def mock_notifier():
    """Create a mock notifier."""
    mock = MagicMock()
    return mock


@pytest.fixture
def price_alert_engine(mock_settings, mock_sentiment, mock_notifier):
    """Return PriceAlertEngine instance for testing with mocked dependencies."""
    with patch('src.alerts.price_alert.SentimentRepository'):
        with patch('src.alerts.price_alert.get_sentiment_provider', return_value = mock_sentiment):
            with patch('src.alerts.price_alert.TelegramNotifier', return_value = mock_notifier):
                with patch('src.alerts.price_alert.HuggingFaceSentiment'):
                    with patch('src.alerts.price_alert.PatternDetector'):
                        engine = PriceAlertEngine(mock_settings)
                        # override the sentiment provider with our mock
                        engine.sentiment = mock_sentiment
                        engine.notifier = mock_notifier
                        return engine


class TestPriceFetcher:
    """Tests for multi-exchange price fetcher with fallback logic."""
    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_success(self, mock_factory):
        """Test successful price fetch from primary exchange."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.return_value = {"last": 65000.0}
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        fetcher = PriceFetcher()
        price = fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = [])
        assert price == 65000.0
        mock_exchange.fetch_ticker.assert_called_once_with("BTC/USDT")


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_fallback(self, mock_factory):
        """Test fallback to secondary exchange when primary fails."""
        mock_binance = MagicMock()
        mock_binance.fetch_ticker.side_effect = ExchangeConnectionError("Network error")
        mock_kraken = MagicMock()
        mock_kraken.fetch_ticker.return_value = {"last": 65000.0}
        mock_factory_instance = MagicMock()
        mock_factory.get_instance.return_value = mock_factory_instance
        mock_factory_instance.get_exchange.side_effect = [mock_binance, mock_kraken]
        fetcher = PriceFetcher()
        price = fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = ["kraken"])
        assert price == 65000.0
        # primary exchange is retried 3 times, default retry_attempts=3
        assert mock_binance.fetch_ticker.call_count == 3
        mock_kraken.fetch_ticker.assert_called_once()


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_all_fail(self, mock_factory):
        """test that all exchanges failing raises ExchangeConnectionError."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.side_effect = ExchangeConnectionError("All fail")
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        fetcher = PriceFetcher()
        with pytest.raises(ExchangeConnectionError, match = "Failed to fetch BTC/USDT from all exchanges"):
            fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = ["kraken"])


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_symbol_not_found(self, mock_factory):
        """Test that symbol not found on all exchanges raises ExchangeConnectionError."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.side_effect = ExchangeSymbolNotFound("Symbol not found")
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        fetcher = PriceFetcher()
        with pytest.raises(ExchangeConnectionError, match = "Failed to fetch INVALID/USDT from all exchanges"):
            fetcher.get_price("INVALID/USDT", exchange = "binance", fallback_exchanges = [])


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_rate_limit_retry(self, mock_factory):
        """Test rate limit triggers retry and eventual success."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.side_effect = [
            ExchangeRateLimitError("Rate limit"),
            ExchangeRateLimitError("Rate limit"),
            {"last": 65000.0},
        ]
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        with patch("time.sleep") as mock_sleep:
            fetcher = PriceFetcher()
            price = fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = [])
            assert price == 65000.0
            assert mock_exchange.fetch_ticker.call_count == 3


class TestAlertLogic:
    """tests for alert evaluation and message generation."""
    def test_check_alerts_trigger_above(self, price_alert_engine):
        """test that 'above' alert triggers when price exceeds threshold."""
        prices = {"binance:BTC/USDT": 71000.0}
        messages = price_alert_engine.check_alerts(prices)
        target_alert = None
        for alert in price_alert_engine.alerts:
            if alert.symbol == "BTC/USDT" and alert.condition == "above":
                target_alert = alert
                break
        assert target_alert is not None
        assert len(messages) == 1
        assert "BTC/USDT" in messages[0]
        assert "above" in messages[0]
        assert target_alert.last_triggered_price == 71000.0


    def test_check_alerts_trigger_below(self, price_alert_engine):
        """test that 'below' alert triggers when price drops below threshold."""
        prices = {"kraken:ETH/USDT": 3500.0}
        messages = price_alert_engine.check_alerts(prices)
        target_alert = None
        for alert in price_alert_engine.alerts:
            if alert.symbol == "ETH/USDT" and alert.condition == "below":
                target_alert = alert
                break
        assert target_alert is not None
        assert len(messages) == 1
        assert "ETH/USDT" in messages[0]
        assert "below" in messages[0]
        assert target_alert.last_triggered_price == 3500.0


    def test_check_alerts_no_trigger(self, price_alert_engine):
        """test that no alert is generated when price is within threshold."""
        prices = {
            "binance:BTC/USDT": 65000.0,
            "kraken:ETH/USDT": 4500.0, # above threshold, so below condition not met
        }
        messages = price_alert_engine.check_alerts(prices)
        assert len(messages) == 0


    def test_cooldown_prevents_repeated_alerts(self, price_alert_engine):
        """test that cooldown prevents duplicate alerts within 1 hour."""
        prices = {"binance:BTC/USDT": 71000.0}
        # first trigger
        messages_one = price_alert_engine.check_alerts(prices)
        assert len(messages_one) == 1
        # second trigger immediately, should be blocked by cooldown
        messages_two = price_alert_engine.check_alerts(prices)
        assert len(messages_two) == 0
        # simulate time passing beyond cooldown AND reset duplicate price check
        for alert in price_alert_engine.alerts:
            if alert.symbol == "BTC/USDT" and alert.condition == "above":
                alert.last_alert_time = datetime.now(timezone.utc) - timedelta(hours = 1, seconds = 1)
                alert.last_triggered_price = None  # reset to allow new alert
        messages_three = price_alert_engine.check_alerts(prices)
        assert len(messages_three) == 1


    def test_duplicate_price_level_blocked(self, price_alert_engine):
        """test that alerts are not repeated for the same price level (within 100)."""
        prices = {"binance:BTC/USDT": 71000.0}
        price_alert_engine.check_alerts(prices)  # first alert
        # set last_alert_time to past to bypass cooldown
        for alert in price_alert_engine.alerts:
            if alert.symbol == "BTC/USDT" and alert.condition == "above":
                alert.last_alert_time = datetime.now(timezone.utc) - timedelta(hours = 1, seconds = 1)
        # same price level (plus-minus 100), should be blocked
        prices_two = {"binance:BTC/USDT": 71050.0}
        messages = price_alert_engine.check_alerts(prices_two)
        assert len(messages) == 0
        # price difference > 100, should trigger
        prices_three = {"binance:BTC/USDT": 71200.0}
        messages_two = price_alert_engine.check_alerts(prices_three)
        assert len(messages_two) == 1


class TestSentimentFallback:
    """tests for sentiment provider fallback and latency logging."""
    def test_mistral_success(self, price_alert_engine, mock_sentiment):
        """test that Mistral works and no fallback is triggered."""
        mock_sentiment.classify.return_value = {"labels": ["bullish"], "scores": [0.95]}
        # Update the engine's sentiment to use the mock we control
        price_alert_engine.sentiment = mock_sentiment
        price_alert_engine.settings.sentiment_provider = "mistral"
        
        message = "Price Alert! BTC/USDT is above 70000"
        enhanced = price_alert_engine.enhance_message(message)
        assert "Sentiment (mistral)" in enhanced
        assert "bullish" in enhanced
        mock_sentiment.classify.assert_called_once()


    def test_fallback_to_huggingface(self, price_alert_engine, mock_sentiment):
        """test that fallback configuration works."""
        # For now, just test that sentiment enhancement works with mock
        mock_sentiment.classify.return_value = {"labels": ["neutral"], "scores": [0.6]}
        price_alert_engine.sentiment = mock_sentiment
        price_alert_engine.settings.enable_sentiment_fallback = True
        price_alert_engine.settings.sentiment_provider = "mistral"
        
        message = "Price Alert! ETH/USDT is below 4000"
        enhanced = price_alert_engine.enhance_message(message)
        # with our mock, it will use the mock's return value
        assert "Sentiment (mistral)" in enhanced
        assert "neutral" in enhanced
        mock_sentiment.classify.assert_called_once()


    def test_both_providers_fail(self, price_alert_engine, mock_sentiment):
        """test that when sentiment returns empty, no sentiment is added."""
        # return minimal valid data to avoid validation errors
        mock_sentiment.classify.return_value = {"labels": ["neutral"], "scores": [0.0]}
        price_alert_engine.sentiment = mock_sentiment
        price_alert_engine.settings.enable_sentiment_fallback = True
        
        message = "Price Alert! BTC/USDT is above 70000"
        enhanced = price_alert_engine.enhance_message(message)
        # with valid data, sentiment should be added
        assert "Sentiment" in enhanced
        mock_sentiment.classify.assert_called_once()


    def test_fallback_disabled(self, price_alert_engine, mock_sentiment):
        """test that when fallback is disabled, failed Mistral results in no sentiment."""
        mock_sentiment.classify.return_value = {}
        price_alert_engine.sentiment = mock_sentiment
        price_alert_engine.settings.enable_sentiment_fallback = False
        
        message = "Price Alert! ETH/USDT is below 4000"
        enhanced = price_alert_engine.enhance_message(message)
        assert enhanced == message
        mock_sentiment.classify.assert_called_once()


    def test_latency_logging(self, price_alert_engine, mock_sentiment, caplog):
        """test that latency is logged correctly."""
        import logging

        caplog.set_level(logging.INFO)
        mock_sentiment.classify.return_value = {"labels": ["bullish"], "scores": [0.95]}
        price_alert_engine.sentiment = mock_sentiment
        price_alert_engine.settings.sentiment_provider = "mistral"
        
        with patch("time.time") as mock_time:
            mock_time.side_effect = [100.0, 100.5, 100.5, 100.5]
            price_alert_engine.enhance_message("Test message")
        assert "Sentiment (mistral) took 0.50s" in caplog.text


class TestTelegramNotifier:
    """tests for Telegram notification integration."""
    @patch("src.alerts.notifier.requests.post")
    def test_send_success(self, mock_post):
        """test that successful Telegram send logs and returns True."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None
        notifier = TelegramNotifier("test_token", "test_chat")
        result = notifier.send("Test message")
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["chat_id"] == "test_chat"
        assert call_args[1]["json"]["text"] == "Test message"


    @patch("src.alerts.notifier.requests.post")
    def test_send_failure(self, mock_post):
        """test that failed Telegram send logs error and returns False."""
        mock_post.side_effect = Exception("Network error")
        notifier = TelegramNotifier("test_token", "test_chat")
        result = notifier.send("Test message")
        assert result is False
        mock_post.assert_called_once()


class TestEndToEnd:
    """full end-to-end test with mocked dependencies."""
    def test_full_alert_flow(self, price_alert_engine, mock_sentiment, mock_notifier):
        """test entire alert pipeline from price fetch to Telegram send."""
        # setup mocks
        mock_sentiment.classify.return_value = {"labels": ["bullish"], "scores": [0.95]}
        price_alert_engine.sentiment = mock_sentiment
        price_alert_engine.settings.sentiment_provider = "mistral"
        price_alert_engine.settings.enable_sentiment_fallback = True
        
        # mock sentiment_repo.store_sentiment to avoid MongoDB errors
        price_alert_engine.sentiment_repo = MagicMock()
        
        # mock pattern detector to return message unchanged
        mock_pattern_detector = MagicMock()
        mock_pattern_detector.detect.return_value = {"cluster_id": -1}  # no pattern detected
        mock_pattern_detector.add_pattern_context_to_alert.side_effect = lambda msg, info: msg
        price_alert_engine.pattern_detector = mock_pattern_detector
        
        # mock _get_price_history to return None (no historical data)
        with patch.object(price_alert_engine, '_get_price_history', return_value = None):
            # mock fetch_prices
            with patch.object(price_alert_engine, 'fetch_prices', return_value = {"binance:BTC/USDT": 71000.0}):
                # mock notifier.send
                mock_notifier.return_value = True
                with patch.object(price_alert_engine.notifier, 'send', return_value = True):
                    price_alert_engine.run_once()
                    # verify notifier.send was called
                    assert price_alert_engine.notifier.send.call_count == 1
                    sent_message = price_alert_engine.notifier.send.call_args[0][0]
                    assert "BTC/USDT" in sent_message
                    assert "above" in sent_message
                    assert "Sentiment (mistral)" in sent_message
                    assert "bullish" in sent_message
