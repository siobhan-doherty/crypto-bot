import requests
import json
import logging
from .base import SentimentProvider

logger = logging.getLogger(__name__)


class MistralSentiment(SentimentProvider):
    def __init__(self, api_key: str, model: str = "open-mistral-7b"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.mistral.ai/v1/chat/completions"


    def classify(self, text: str) -> dict:
        prompt = f"""
        Classify sentiment of this cryptocurrency price alert.
        Return only JSON with keys: sentiment (bullish/bearish/neutral) and confidence (0-1).
        Text: {text}
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 50,
            "response_format": {"type": "json_object"}
        }
        try:
            resp = requests.post(self.base_url, json = payload, headers = headers, timeout = 10)
            resp.raise_for_status()
            data = resp.json()
            # extract token usage if available, Mistral returns usage
            usage = data.get("usage", {})
            if usage:
                logger.debug(f"Mistral token usage: {usage}")
            result = json.loads(data["choices"][0]["message"]["content"])
            return {
                "labels": [result.get("sentiment", "neutral")],
                "scores": [result.get("confidence", 0.5)],
                "usage": usage  # pass for cost
            }

        except Exception as e:
            logger.warning(f"Mistral classification failed: {e}")
            return {}
