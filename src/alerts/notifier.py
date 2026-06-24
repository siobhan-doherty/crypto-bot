import requests
import logging

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"


    def send(self, message: str) -> bool:
        """Send a plain text message via Telegram."""
        try:
            resp = requests.post(
                self.api_url,
                json = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"},
                timeout = 10,
            )
            resp.raise_for_status()
            logger.info(f"Telegram alert sent: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False


class HuggingFaceEnhancer:
    """Optional: enrich alerts with sentiment or news classification."""
    def __init__(self, token: str, model: str = "facebook/bart-large-mnli"):
        self.token = token
        self.model = model
        self.api_url = f"https://api-inference.huggingface.co/models/{model}"


    def classify(self, text: str, labels: list[str]) -> dict:
        """Zero-shot classification of price-related sentence."""
        if not self.token:
            return {}
        try:
            resp = requests.post(
                self.api_url,
                headers = {"Authorization": f"Bearer {self.token}"},
                json = {"inputs": text, "parameters": {"candidate_labels": labels}},
                timeout = 10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"HF classification failed: {e}")
            return {}
