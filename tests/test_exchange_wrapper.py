"""Tests for the multi-exchange wrapper module."""
import pytest
from unittest.mock import MagicMock, patch
from src.exchange_wrapper import get_price
from src.exchange_wrapper.config import ExchangeWrapperConfig
from src.exchange_wrapper.exceptions import (
    ExchangeConnectionError,
    ExchangeError,
    ExchangeRateLimitError,
    ExchangeSymbolNotFound,
)
from src.exchange_wrapper.exchange_factory import ExchangeFactory
from src.exchange_wrapper.price_fetcher import PriceFetcher


class TestExchangeConfig:
    """Tests for ExchangeWrapperConfig."""
    def test_default_config(self):
        """Test default configuration values."""
        config = ExchangeWrapperConfig()
        assert config.default_exchange == "binance"
        assert config.timeout_seconds == 10
        assert config.retry_attempts == 3
        assert config.retry_backoff_factor == 0.5
        assert config.enable_cache is True
        assert config.cache_ttl_seconds == 5


    def test_config_with_env_prefix(self):
        """Test that config uses EXCHANGE_ prefix for environment variables."""
        # check class-level model_config has env_prefix
        assert ExchangeWrapperConfig.model_config["env_prefix"] == "EXCHANGE_"


class TestExchangeFactory:
    """Tests for ExchangeFactory singleton."""
    def test_singleton_pattern(self):
        """Test that ExchangeFactory is a singleton."""
        factory1 = ExchangeFactory.get_instance()
        factory2 = ExchangeFactory.get_instance()
        assert factory1 is factory2


    @patch("src.exchange_wrapper.exchange_factory.ccxt")
    def test_init_exchanges(self, mock_ccxt):
        """Test exchange initialization."""
        # Setup mock exchanges
        mock_binance = MagicMock()
        mock_kraken = MagicMock()
        mock_ccxt.binance = mock_binance
        mock_ccxt.kraken = mock_kraken
        mock_ccxt.bitmex = MagicMock()
        mock_ccxt.bybit = MagicMock()
        # reset singleton for this test
        ExchangeFactory._instance = None
        ExchangeFactory._exchanges = {}
        factory = ExchangeFactory.get_instance()
        # verify exchanges were initialized
        assert "binance" in factory._exchanges
        assert "kraken" in factory._exchanges
        assert "bitmex" in factory._exchanges
        assert "bybit" in factory._exchanges


    @patch("src.exchange_wrapper.exchange_factory.ccxt")
    def test_get_exchange(self, mock_ccxt):
        """Test getting a specific exchange."""
        mock_binance = MagicMock()
        mock_ccxt.binance = mock_binance
        mock_ccxt.kraken = MagicMock()
        mock_ccxt.bitmex = MagicMock()
        mock_ccxt.bybit = MagicMock()
        # reset singleton
        ExchangeFactory._instance = None
        ExchangeFactory._exchanges = {}
        factory = ExchangeFactory.get_instance()
        exchange = factory.get_exchange("binance")
        assert exchange is not None


    @patch("src.exchange_wrapper.exchange_factory.ccxt")
    def test_get_unsupported_exchange(self, mock_ccxt):
        """Test that getting an unsupported exchange raises ValueError."""
        mock_ccxt.binance = MagicMock()
        mock_ccxt.kraken = MagicMock()
        mock_ccxt.bitmex = MagicMock()
        mock_ccxt.bybit = MagicMock()
        # reset singleton
        ExchangeFactory._instance = None
        ExchangeFactory._exchanges = {}
        factory = ExchangeFactory.get_instance()
        with pytest.raises(ValueError, match = "Unsupported exchange"):
            factory.get_exchange("unsupported_exchange")


class TestPriceFetcher:
    """Tests for PriceFetcher with multi-exchange support."""
    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_success(self, mock_factory):
        """Test successful price fetch from primary exchange."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.return_value = {"last": 65000.0}
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        # create a new PriceFetcher, not using singleton to avoid side effects
        fetcher = PriceFetcher()
        fetcher.factory = mock_factory.get_instance()
        price = fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = [])
        assert price == 65000.0
        mock_exchange.fetch_ticker.assert_called_once_with("BTC/USDT")


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_with_fallback(self, mock_factory):
        """Test fallback to secondary exchange when primary fails."""
        mock_binance = MagicMock()
        mock_binance.fetch_ticker.side_effect = ExchangeConnectionError("Network error")
        mock_kraken = MagicMock()
        mock_kraken.fetch_ticker.return_value = {"last": 65000.0}
        mock_factory_instance = MagicMock()
        mock_factory.get_instance.return_value = mock_factory_instance
        mock_factory_instance.get_exchange.side_effect = lambda name: mock_binance if name == "binance" else mock_kraken
        fetcher = PriceFetcher()
        fetcher.factory = mock_factory_instance
        price = fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = ["kraken"])
        assert price == 65000.0
        # primary exchange is retried 3 times by default
        assert mock_binance.fetch_ticker.call_count == 3
        mock_kraken.fetch_ticker.assert_called_once()


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_all_exchanges_fail(self, mock_factory):
        """Test that all exchanges failing raises ExchangeConnectionError."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.side_effect = ExchangeConnectionError("All fail")
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        fetcher = PriceFetcher()
        fetcher.factory = mock_factory.get_instance()
        with pytest.raises(ExchangeConnectionError, match = "Failed to fetch BTC/USDT from all exchanges"):
            fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = ["kraken"])


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_symbol_not_found(self, mock_factory):
        """Test that symbol not found raises appropriate error."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.side_effect = ExchangeSymbolNotFound("Symbol not found")
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        fetcher = PriceFetcher()
        fetcher.factory = mock_factory.get_instance()
        with pytest.raises(ExchangeConnectionError, match = "Failed to fetch INVALID/USDT from all exchanges"):
            fetcher.get_price("INVALID/USDT", exchange = "binance", fallback_exchanges = [])


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    @patch("time.sleep")
    def test_get_price_rate_limit_retry(self, mock_sleep, mock_factory):
        """Test rate limit triggers retry and eventual success."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.side_effect = [
            ExchangeRateLimitError("Rate limit"),
            ExchangeRateLimitError("Rate limit"),
            {"last": 65000.0},
        ]
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        fetcher = PriceFetcher()
        fetcher.factory = mock_factory.get_instance()
        price = fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = [])
        assert price == 65000.0
        assert mock_exchange.fetch_ticker.call_count == 3


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_cache_hit(self, mock_factory):
        """Test that cached prices are returned."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.return_value = {"last": 65000.0}
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        fetcher = PriceFetcher()
        fetcher.factory = mock_factory.get_instance()
        fetcher.config.cache_ttl_seconds = 10
        fetcher.config.enable_cache = True
        # first call, should fetch from exchange
        price1 = fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = [])
        assert price1 == 65000.0
        assert mock_exchange.fetch_ticker.call_count == 1
        # second call, should use cache
        price2 = fetcher.get_price("BTC/USDT", exchange = "binance", fallback_exchanges = [])
        assert price2 == 65000.0
        # should still be 1 because second call used cache
        assert mock_exchange.fetch_ticker.call_count == 1


class TestGetPriceConvenienceFunction:
    """Tests for the get_price convenience function."""
    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_function(self, mock_factory):
        """Test the module-level get_price function."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.return_value = {"last": 50000.0}
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        # need to patch singleton price fetcher
        with patch("src.exchange_wrapper.price_fetcher._price_fetcher") as mock_fetcher:
            mock_fetcher.get_price.return_value = 50000.0
            price = get_price("BTC/USDT")
            assert price == 50000.0
            mock_fetcher.get_price.assert_called_once_with("BTC/USDT", None, None)


    @patch("src.exchange_wrapper.price_fetcher.ExchangeFactory")
    def test_get_price_with_exchange_and_fallback(self, mock_factory):
        """Test get_price with explicit exchange and fallback."""
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker.return_value = {"last": 55000.0}
        mock_factory.get_instance().get_exchange.return_value = mock_exchange
        with patch("src.exchange_wrapper.price_fetcher._price_fetcher") as mock_fetcher:
            mock_fetcher.get_price.return_value = 55000.0
            price = get_price("ETH/USDT", exchange = "kraken", fallback_exchanges = ["binance"])
            assert price == 55000.0
            mock_fetcher.get_price.assert_called_once_with(
                "ETH/USDT", "kraken", ["binance"]
            )


class TestExchangeExceptions:
    """Tests for custom exception classes."""
    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from ExchangeError."""
        assert issubclass(ExchangeConnectionError, ExchangeError)
        assert issubclass(ExchangeSymbolNotFound, ExchangeError)
        assert issubclass(ExchangeRateLimitError, ExchangeError)


    def test_exception_messages(self):
        """Test that exceptions can carry messages."""
        msg = "Test error message"
        assert str(ExchangeError(msg)) == msg
        assert str(ExchangeConnectionError(msg)) == msg
        assert str(ExchangeSymbolNotFound(msg)) == msg
        assert str(ExchangeRateLimitError(msg)) == msg
