from .base import SentimentProvider
from .mistral import MistralSentiment
from .huggingface import HuggingFaceSentiment
from src.alerts.config import AlertSettings


def get_sentiment_provider(settings: AlertSettings) -> SentimentProvider:
    provider = settings.sentiment_provider.lower()
    if provider == "mistral":
        return MistralSentiment(settings.mistral_api_key, settings.mistral_model)

    else:
        # default to HF
        return HuggingFaceSentiment(settings.hf_token, settings.hf_model)
