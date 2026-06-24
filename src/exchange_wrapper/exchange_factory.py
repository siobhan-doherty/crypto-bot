import ccxt
import logging
from functools import lru_cache
from typing import Dict, Optional
from .config import ExchangeWrapperConfig
from .exceptions import ExchangeConnectionError

logger = logging.getLogger(__name__)


class ExchangeFactory:
    """Singleton factory that caches CCXT exchange instances."""
    _instance: Optional["ExchangeFactory"] = None
    _exchanges: Dict[str, ccxt.Exchange] = {}


    def __new__(cls) -> "ExchangeFactory":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self):
        self.config = ExchangeWrapperConfig()
        self._init_exchanges()


    def _init_exchanges(self) -> None:
        """Initialize all supported exchanges with common settings."""
        exchange_classes = {
            "binance": ccxt.binance,
            "kraken": ccxt.kraken,
            "coinbase": ccxt.coinbase,
        }

        for name, cls_ in exchange_classes.items():
            try:
                exchange = cls_({
                    "timeout": self.config.timeout_seconds * 1000,  # CCXT expects ms
                    "enableRateLimit": True,
                    "options": {"defaultType": "spot"},
                })

                # add API keys if present
                api_key = getattr(self.config, f"{name}_api_key", "")
                api_secret = getattr(self.config, f"{name}_api_secret", "")
                if api_key and api_secret:
                    exchange.apiKey = api_key
                    exchange.secret = api_secret
                    # coinbase also needs passphrase
                    if name == "coinbase":
                        exchange.password = self.config.coinbase_passphrase

                self._exchanges[name] = exchange
                logger.info(f"Initialized exchange: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")


    def get_exchange(self, exchange_name: str) -> ccxt.Exchange:
        """Return a CCXT exchange instance by name."""
        if exchange_name not in self._exchanges:
            raise ValueError(f"Unsupported exchange: {exchange_name}")
        return self._exchanges[exchange_name]


    @staticmethod
    def get_instance() -> "ExchangeFactory":
        """Return the singleton instance."""
        return ExchangeFactory()
