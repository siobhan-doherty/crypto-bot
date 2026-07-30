"""Unit tests for TelegramNotifier."""
import pytest
from unittest.mock import MagicMock, patch
from src.alerts.notifier import TelegramNotifier


@pytest.fixture
def mock_notifier():
    """Create a TelegramNotifier with mocked requests."""
    with patch('src.alerts.notifier.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        return TelegramNotifier("test_token", "test_chat_id")


def test_notifier_init():
    """Test notifier initialization."""
    notifier = TelegramNotifier("test_token", "test_chat_id")
    assert notifier.bot_token == "test_token"
    assert notifier.chat_id == "test_chat_id"


def test_send_success():
    """Test successful message sending."""
    with patch('src.alerts.notifier.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        notifier = TelegramNotifier("test_token", "test_chat_id")
        result = notifier.send("Test message")
        assert result is True
        mock_post.assert_called_once()


def test_send_failure():
    """Test message sending failure."""
    with patch('src.alerts.notifier.requests.post') as mock_post:
        mock_post.side_effect = Exception("API Error")

        notifier = TelegramNotifier("test_token", "test_chat_id")
        result = notifier.send("Test message")
        assert result is False


def test_send_empty_message():
    """Test sending empty message - should return False."""
    with patch('src.alerts.notifier.requests.post') as mock_post:
        notifier = TelegramNotifier("test_token", "test_chat_id")
        # Empty or whitespace-only messages should return False
        result = notifier.send("")
        assert result is False
        mock_post.assert_not_called()

def test_send_whitespace_message():
    """Test sending whitespace-only message."""
    with patch('src.alerts.notifier.requests.post') as mock_post:
        notifier = TelegramNotifier("test_token", "test_chat_id")
        result = notifier.send("   ")
        assert result is False
        mock_post.assert_not_called()

def test_send_long_message():
    """Test sending long message (should be truncated)."""
    long_message = "x" * 5000  # Telegram max is ~4096
    with patch('src.alerts.notifier.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        notifier = TelegramNotifier("test_token", "test_chat_id")
        result = notifier.send(long_message)
        assert result is True
        mock_post.assert_called_once()
        # Verify the message was truncated
        call_args = mock_post.call_args[1]
        assert 'json' in call_args
        assert len(call_args['json']['text']) <= 4096
