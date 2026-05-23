from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    LOG_LEVEL: str = "INFO"
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    BINANCE_SYMBOLS: List[str] = ["BTCUSDT", "ETHUSDT"]
    KAFKA_INTERVAL: str = "1m"
    KAFKA_TOPIC: str = "binance_prices"
    KAFKA_CONSUMER_GROUP: str = "binance-group"

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra = "ignore"
    )

settings = Settings()
