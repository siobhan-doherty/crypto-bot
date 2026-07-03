import requests
import logging
from .base import SentimentProvider

logger = logging.getLogger(__name__)


class HuggingFaceSentiment(SentimentProvider):
    def __init__(self, token: str, model: str = "facebook/bart-large-mnli"):
        self.token = token
        self.model = model
        self.api_url = f"https://api-inference.huggingface.co/models/{model}"


    def classify(self, text: str) -> dict:
        if not self.token:
            return {}

        try:
            resp = requests.post(
                self.api_url,
                headers = {"Authorization": f"Bearer {self.token}"},
                json = {
                    "inputs": text,
                    "parameters": {"candidate_labels": ["bullish", "bearish", "neutral"]}
                },
                timeout = 10,
            )
            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            logger.warning(f"HF classification failed: {e}")
            return {}
