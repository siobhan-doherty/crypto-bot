"""Unit tests for sentiment providers."""
import pytest
from unittest.mock import MagicMock, patch
from src.alerts.sentiment.mistral import MistralSentiment
from src.alerts.sentiment.huggingface import HuggingFaceSentiment


def test_mistral_sentiment_init():
    """Test MistralSentiment initialization."""
    provider = MistralSentiment("test_api_key", "test_model")
    assert provider.api_key == "test_api_key"
    assert provider.model == "test_model"
    assert provider.base_url == "https://api.mistral.ai/v1/chat/completions"


def test_mistral_classify_success():
    """Test successful Mistral classification."""
    with patch('src.alerts.sentiment.mistral.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"sentiment": "bullish", "confidence": 0.85}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        provider = MistralSentiment("test_api_key", "test_model")
        result = provider.classify("Test message")
        assert result["labels"][0] == "bullish"
        assert result["scores"][0] == 0.85
        assert "usage" in result


def test_mistral_classify_failure():
    """Test Mistral classification failure."""
    with patch('src.alerts.sentiment.mistral.requests.post') as mock_post:
        mock_post.side_effect = Exception("API Error")
        provider = MistralSentiment("test_api_key", "test_model")
        result = provider.classify("Test message")
        assert result == {}


def test_huggingface_sentiment_init():
    """Test HuggingFaceSentiment initialization."""
    provider = HuggingFaceSentiment("test_token", "test_model")
    assert provider.token == "test_token"
    assert provider.model == "test_model"


def test_huggingface_classify_success():
    """Test successful HuggingFace classification."""
    with patch('src.alerts.sentiment.huggingface.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "labels": ["positive", "negative"],
            "scores": [0.9, 0.1]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        provider = HuggingFaceSentiment("test_token", "test_model")
        result = provider.classify("Test message")
        assert result["labels"] == ["positive", "negative"]
        assert result["scores"] == [0.9, 0.1]


def test_huggingface_classify_failure():
    """Test HuggingFace classification failure."""
    with patch('src.alerts.sentiment.huggingface.requests.post') as mock_post:
        mock_post.side_effect = Exception("API Error")
        provider = HuggingFaceSentiment("test_token", "test_model")
        result = provider.classify("Test message")
        assert result == {}
