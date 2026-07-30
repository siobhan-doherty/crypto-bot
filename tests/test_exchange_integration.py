"""Integration tests for multi-exchange wrapper wiring."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.alerts.config import AlertSettings
from src.alerts.price_alert import PriceAlertEngine
from src.exchange_wrapper import get_price
from src.exchange_wrapper.exceptions import ExchangeConnectionError


@pytest.fixture
def mock_settings_with_exchanges(tmp_path):
    """Create AlertSettings with multi-exchange alert configuration."""
    alerts_data = [
        {
            "symbol": "BTC/USDT",
            "exchange": "binance",
            "threshold": 70000.0,
            "condition": "above",
            "fallback_exchanges": ["kraken", "bybit"],
        },
        {
            "symbol": "ETH/USDT",
            "exchange": "kraken",
            "threshold": 4000.0,
            "condition": "below",
            "fallback_exchanges": ["binance", "bybit"],
        },
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
        default_fallback_exchanges = ["binance", "kraken", "bybit"],
        sentiment_provider = "huggingface",  # use HF to avoid API calls
        enable_sentiment_fallback = False,
        mongo_uri = "mongodb://localhost:27017/test",
    )
    return settings


class TestExchangeWrapperWiring:
    """Test that multi-exchange wrapper is properly wired into the alert system."""
    @patch("src.alerts.price_alert.get_price")
    def test_fetch_prices_uses_exchange_wrapper(self, mock_get_price, mock_settings_with_exchanges):
        """Test that fetch_prices calls get_price from exchange_wrapper."""
        mock_get_price.side_effect = [71000.0, 3500.0]
        engine = PriceAlertEngine(mock_settings_with_exchanges)
        prices = engine.fetch_prices()
        assert len(prices) == 2
        assert prices.get("binance:BTC/USDT") == 71000.0
        assert prices.get("kraken:ETH/USDT") == 3500.0

        # verify get_price was called with correct parameters
        calls = mock_get_price.call_args_list
        assert len(calls) == 2

        # first call for BTC/USDT on binance with fallback
        first_call = calls[0]
        assert first_call[1]["symbol"] == "BTC/USDT"
        assert first_call[1]["exchange"] == "binance"
        assert first_call[1]["fallback_exchanges"] == ["kraken", "bybit"]

        # second call for ETH/USDT on kraken with fallback
        second_call = calls[1]
        assert second_call[1]["symbol"] == "ETH/USDT"
        assert second_call[1]["exchange"] == "kraken"
        assert second_call[1]["fallback_exchanges"] == ["binance", "bybit"]


    @patch("src.alerts.price_alert.get_price")
    def test_fetch_prices_handles_failures(self, mock_get_price, mock_settings_with_exchanges):
        """Test that fetch_prices handles exchange failures gracefully."""
        # simulate first price succeeds, second fails
        mock_get_price.side_effect = [
            71000.0,
            ExchangeConnectionError("Failed to fetch ETH/USDT from all exchanges: ['kraken', 'binance', 'bybit']"),
        ]
        engine = PriceAlertEngine(mock_settings_with_exchanges)
        prices = engine.fetch_prices()
        # should only have successful price
        assert len(prices) == 1
        assert prices.get("binance:BTC/USDT") == 71000.0
        assert "kraken:ETH/USDT" not in prices


    @patch("src.alerts.price_alert.get_price")
    def test_fetch_prices_deduplicates_symbols(self, mock_get_price, mock_settings_with_exchanges):
        """Test that fetch_prices doesn't fetch same symbol twice from same exchange."""
        mock_get_price.side_effect = [71000.0, 3500.0, 72000.0]
        # add duplicate alert for same symbol on same exchange
        alerts_data = [
            {
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "threshold": 70000.0,
                "condition": "above",
                "fallback_exchanges": ["kraken"],
            },
            {
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "threshold": 75000.0,
                "condition": "above",
                "fallback_exchanges": ["kraken"],
            },
            {
                "symbol": "ETH/USDT",
                "exchange": "kraken",
                "threshold": 4000.0,
                "condition": "below",
            },
        ]
        alerts_file = Path(mock_settings_with_exchanges.alerts_file)
        alerts_file.write_text(json.dumps(alerts_data))
        mock_settings_with_exchanges.alerts_file = str(alerts_file)
        engine = PriceAlertEngine(mock_settings_with_exchanges)
        prices = engine.fetch_prices()
        # should only have 2 unique symbol:exchange combinations
        assert len(prices) == 2
        assert "binance:BTC/USDT" in prices
        assert "kraken:ETH/USDT" in prices

        # get_price should only be called twice
        assert mock_get_price.call_count == 2


    @patch("src.alerts.price_alert.get_price")
    def test_fetch_prices_uses_default_fallback(self, mock_get_price, mock_settings_with_exchanges):
        """Test that alerts without fallback_exchanges use default_fallback_exchanges."""
        # modify settings to have alerts without fallback_exchanges
        alerts_data = [
            {
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "threshold": 70000.0,
                "condition": "above",
                # no fallback_exchanges specified
            },
        ]
        alerts_file = Path(mock_settings_with_exchanges.alerts_file)
        alerts_file.write_text(json.dumps(alerts_data))
        mock_settings_with_exchanges.alerts_file = str(alerts_file)
        mock_get_price.side_effect = [71000.0]
        engine = PriceAlertEngine(mock_settings_with_exchanges)
        prices = engine.fetch_prices()
        # verify default fallback was used
        call = mock_get_price.call_args_list[0]
        assert call[1]["fallback_exchanges"] == ["binance", "kraken", "bybit"]


class TestEndToEndWiring:
    """End-to-end wiring test with mocked CCXT."""
    @patch("src.exchange_wrapper.exchange_factory.ccxt")
    def test_get_price_uses_ccxt(self, mock_ccxt):
        """Test that get_price ultimately uses CCXT exchanges."""
        # setup mock CCXT exchange
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.return_value = {"last": 50000.0}
        mock_ccxt.binance = lambda config=None: mock_exchange
        mock_ccxt.kraken = MagicMock()
        mock_ccxt.bitmex = MagicMock()
        mock_ccxt.bybit = MagicMock()
        # reset singleton factory for this test
        from src.exchange_wrapper.exchange_factory import ExchangeFactory
        ExchangeFactory._instance = None
        ExchangeFactory._exchanges = {}
        # now call get_price, it should create factory, get exchange, fetch price
        # we need to patch the singleton price fetcher to use a fresh one
        with patch("src.exchange_wrapper.price_fetcher._price_fetcher") as mock_fetcher:
            # create a fresh PriceFetcher that will use the real factory
            from src.exchange_wrapper.price_fetcher import PriceFetcher
            fresh_fetcher = PriceFetcher()
            mock_fetcher.get_price.side_effect = fresh_fetcher.get_price
            price = get_price("BTC/USDT", exchange = "binance", fallback_exchanges = [])
            assert price == 50000.0
            mock_exchange.fetch_ticker.assert_called_once_with("BTC/USDT")
