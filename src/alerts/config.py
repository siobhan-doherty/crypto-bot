import json
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Any


class AlertSettings(BaseSettings):
    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""          # personal chat ID
    # Hugging Face
    hf_token: str = ""
    hf_model: str = "facebook/bart-large-mnli"
    alerts_file: str = "alerts.json"
    # how often to check prices
    check_interval_seconds: int = 60
    # default fallback exchanged, used if alert does not specify its own
    default_fallback_exchanges: List[str] = ["binance", "kraken"]

    @property
    def alerts(self) -> List[dict]:
        """Load alerts from JSON file."""
        path = Path(self.alerts_file)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        # fallback to default alerts, so it works out of the box
        return [
            {"symbol": "BTC/USDT", "exchange": "binance", "threshold": 70000.0, "condition": "above"},
            {"symbol": "ETH/USDT", "exchange": "binance", "threshold": 4000.0, "condition": "above"},
        ]

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_prefix = "ALERT_",
        extra = "ignore",  
    ) 
