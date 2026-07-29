import json
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class AlertSettings(BaseSettings):
    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    # Hugging Face
    hf_token: str = ""
    hf_model: str = "facebook/bart-large-mnli"
    # Mistral AI
    sentiment_provider: str = "mistral"
    mistral_api_key: str = ""
    mistral_model: str = "open-mistral-7b"
    enable_sentiment_fallback: bool = True
    # Alerts
    alerts_file: str = "alerts.json"
    check_interval_seconds: int = 60
    default_fallback_exchanges: List[str] = ["binance", "kraken", "bybit"]
    # MongoDB, for sentiment history
    mongo_uri: str = ""
    sentiment_retention_seconds: int = 365 * 24 * 60 * 60  # 1 year default
    # MongoDB authentication
    mongo_username: str = ""
    mongo_password: str = ""
    mongo_host: str = "mongodb"
    mongo_port: int = 27017
    mongo_database: str = "cryptobot"

    @property
    def alerts(self) -> List[dict]:
        path = Path(self.alerts_file)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return [
            {"symbol": "BTC/USDT", "exchange": "binance", "threshold": 70000.0, "condition": "above"},
            {"symbol": "ETH/USDT", "exchange": "binance", "threshold": 4000.0, "condition": "above"},
        ]

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_prefix = "ALERT_",
        extra = "ignore",
    )
