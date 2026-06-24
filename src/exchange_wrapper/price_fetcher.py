import logging
import time
from functools import lru_cache
from typing import Dict, Optional, Union
from .config import ExchangeWrapperConfig
from .exchange_factory import ExchangeFactory
from .exceptions import ExchangeConnectionError, ExchangeSymbolNotFound, ExchangeRateLimitError

logger = logging.getLogger(__name__)


class PriceFetcher:
    """Thread‑safe price fetcher handling retries, caching and exchange‑specific symbol mapping."""
    # map common symbol formats to exchange-specific ones if needed
    # CCXT usually accepts standard formats like BTC/USDT, but some exchanges differ.
    _symbol_mapping: Dict[str, Dict[str, str]] = {
        "binance": {
            # no mapping needed for Binance, uses BTC/USDT
        },
        "kraken": {
            # Kraken uses XBT/USD for Bitcoin but CCXT also accepts BTC/USD
            # keep simple, CCXT handles most conversions
        },
        "coinbase": {
            # coinbase uses BTC-USD for their API however CCXT accepts BTC/USD
        },
    }


    def __init__(self):
        self.config = ExchangeWrapperConfig()
        self.factory = ExchangeFactory.get_instance()
        self._cache: Dict[str, tuple[float, float]] = {}  # key -> (price, timestamp)


    def _get_cached_price(self, key: str) -> Optional[float]:
        """Return cached price if still valid."""
        if not self.config.enable_cache:
            return None
        if key in self._cache:
            price, timestamp = self._cache[key]
            if time.time() - timestamp < self.config.cache_ttl_seconds:
                return price
            else:
                del self._cache[key]
        return None


    def _set_cache(self, key: str, price: float) -> None:
        if self.config.enable_cache:
            self._cache[key] = (price, time.time())


    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Ensure symbol uses '/' separator CCXT standard."""
        if "/" not in symbol:
            # assume like BTCUSDT, convert to BTC/USDT for CCXT (for prod. one may want mapping)
            # assume inputs already in CCXT format
            pass
        return symbol


    def get_price(
        self,
        symbol: str,
        exchange: Optional[str] = None,
        fallback_exchanges: Optional[list[str]] = None,
    ) -> float:
        """
        Fetch the current price (last trade) for a symbol from the specified exchange.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT", "ETH/BTC").
            exchange: Name of the primary exchange to use (e.g., "binance").
                    If None, uses the default from config.
            fallback_exchanges: List of exchanges to try if the primary fails.
                                If None, defaults to all supported exchanges (except the primary).

        Returns:
            The last price as a float.

        Raises:
            ExchangeConnectionError: If all exchange attempts fail.
            ExchangeSymbolNotFound: If the symbol is not found on any exchange.
        """
        if exchange is None:
            exchange = self.config.default_exchange

        if fallback_exchanges is None:
            fallback_exchanges = ["binance", "kraken", "coinbase"]
            # remove primary to avoid duplicate attempts
            fallback_exchanges = [ex for ex in fallback_exchanges if ex != exchange]
        # build try order
        exchanges_to_try = [exchange] + fallback_exchanges

        for ex_name in exchanges_to_try:
            try:
                price = self._fetch_from_exchange(symbol, ex_name)
                if price is not None:
                    return price
            except (ExchangeConnectionError, ExchangeSymbolNotFound, ExchangeRateLimitError) as e:
                logger.warning(f"Failed to fetch from {ex_name}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error from {ex_name}: {e}")
                continue

        raise ExchangeConnectionError(
            f"Failed to fetch {symbol} from all exchanges: {exchanges_to_try}"
        )


    def _fetch_from_exchange(self, symbol: str, exchange_name: str) -> Optional[float]:
        """Internal method to fetch from single exchange with retries."""
        cache_key = f"{exchange_name}:{symbol}"
        cached = self._get_cached_price(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached

        exchange = self.factory.get_exchange(exchange_name)
        retries = self.config.retry_attempts
        backoff = self.config.retry_backoff_factor

        for attempt in range(retries):
            try:
                # CCXT's fetch_ticker returns dict with last price
                ticker = exchange.fetch_ticker(symbol)
                if ticker is None or ticker.get("last") is None:
                    raise ExchangeSymbolNotFound(f"Symbol {symbol} not found on {exchange_name}")

                price = float(ticker["last"])
                self._set_cache(cache_key, price)
                logger.info(f"Fetched {symbol} from {exchange_name}: {price}")
                return price

            except ccxt.BadSymbol:
                raise ExchangeSymbolNotFound(f"Symbol {symbol} not found on {exchange_name}")
            except ccxt.RateLimitExceeded:
                raise ExchangeRateLimitError(f"Rate limit exceeded on {exchange_name}")
            except ccxt.NetworkError as e:
                raise ExchangeConnectionError(f"Network error from {exchange_name}: {e}")
            except ccxt.ExchangeError as e:
                # more generic error, could be temporary, retry
                if attempt < retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    logger.warning(
                        f"Exchange error from {exchange_name} (attempt {attempt+1}/{retries}): {e}. "
                        f"Retrying in {sleep_time}s"
                    )
                    time.sleep(sleep_time)
                    continue
                else:
                    raise ExchangeConnectionError(f"Exchange error: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                if attempt < retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    time.sleep(sleep_time)
                    continue
                raise

        return None # should not reach here

# convenience singleton
_price_fetcher = PriceFetcher()


def get_price(
        symbol: str, 
        exchange: Optional[str] = None, 
        fallback_exchanges: Optional[list[str]] = None
) -> float:
    """
    Public interface to fetch price.

    Example:
        >>> price = get_price("BTC/USDT", exchange="binance")
        >>> print(price)
        65000.0

        >>> # with fallbacks
        >>> price = get_price("BTC/USDT", exchange="kraken", fallback_exchanges=["coinbase"])
    """
    return _price_fetcher.get_price(symbol, exchange, fallback_exchanges)
