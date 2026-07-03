from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class ExchangeWrapperConfig(BaseSettings):
    default_exchange: str = "binance"
    timeout_seconds: int = 10
    retry_attempts: int = 3
    retry_backoff_factor: float = 0.5
    enable_cache: bool = True
    cache_ttl_seconds: int = 5   # cache price for 5 seconds to avoid redundant calls

    # API keys
    binance_api_key: str = ""
    binance_api_secret: str = ""
    kraken_api_key: str = ""
    kraken_api_secret: str = ""
    bybit_api_key: str = ""
    bybit_api_secret: str = ""
    bitmex_api_key: str = ""
    bitmex_api_secret: str = ""

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_prefix = "EXCHANGE_",
        extra = "ignore",  # Ignore extra environment variables
    )
