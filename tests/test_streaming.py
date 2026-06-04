from unittest.mock import MagicMock

from api_user.streaming import fetch_data


def test_fetch_data_with_filters():
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.find.return_value = mock_cursor
    mock_cursor.__iter__.return_value = []

    result = fetch_data(mock_collection, minutes=60, filters={"symbol": "BTCUSDT"})

    mock_collection.find.assert_called_once()
    call_args = mock_collection.find.call_args[0][0]
    assert "symbol" in call_args
    assert "close_datetime" in call_args
    assert result == []


def test_fetch_data_no_filters():
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.find.return_value = mock_cursor
    mock_cursor.__iter__.return_value = []

    result = fetch_data(mock_collection, minutes=60, filters=None)

    mock_collection.find.assert_called_once()
    call_args = mock_collection.find.call_args[0][0]
    assert "close_datetime" in call_args
    assert "symbol" not in call_args
    assert result == []


def test_fetch_data_handles_exception():
    mock_collection = MagicMock()
    mock_collection.find.side_effect = Exception("DB error")
    result = fetch_data(mock_collection, minutes=60)
    assert result == []  # graceful fallback
