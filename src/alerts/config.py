from pydantic_settings import BaseSettings


class AlertSettings(BaseSettings):
    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""          # personal chat ID

    # Hugging Face
    hf_token: str = ""
    hf_model: str = "facebook/bart-large-mnli"  # zero-shot classifier

    # alert parameters
    symbols: list[str] = ["BTC/USDT", "ETH/USDT"]
    check_interval_seconds: int = 60
    price_threshold_above: float = 70000.0   # alert when BTC > 70k
    price_threshold_below: float = 60000.0   # alert when BTC < 60k

    class Config:
        env_file = ".env"
        env_prefix = "ALERT_"
