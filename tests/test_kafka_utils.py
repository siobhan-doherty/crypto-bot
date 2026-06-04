from unittest.mock import patch

import pytest

from collection_admin.kafka_utils import kline_to_dict, wait_for_kafka


def test_wait_for_kafka_success():
    with patch("socket.create_connection") as mock_connect:
        wait_for_kafka("localhost", 9092, timeout=2)
        mock_connect.assert_called_once()


def test_wait_for_kafka_timeout():
    with patch("socket.create_connection", side_effect=Exception):
        with pytest.raises(TimeoutError):
            wait_for_kafka("localhost", 9092, timeout=1)


def test_kline_to_dict():
    sample = {
        "s": "BTCUSDT",
        "k": {
            "t": 1620000000000,
            "T": 1620000060000,
            "o": "50000",
            "c": "50100",
            "h": "50200",
            "l": "49900",
            "v": "1.5",
            "q": "75000",
            "n": 120,
            "V": "0.8",
            "Q": "40000",
            "x": True,
        },
    }
    result = kline_to_dict(sample)
    assert result["symbol"] == "BTCUSDT"
    assert result["open"] == 50000.0
    assert result["close"] == 50100.0
    assert result["is_closed"] is True
    assert "open_datetime" in result
