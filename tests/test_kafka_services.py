from unittest.mock import MagicMock, patch

import pytest

from collection_admin.data.kafka_consumer import KafkaConsumerService
from collection_admin.data.kafka_producer import KafkaProducerService
from collection_admin.kafka_utils import kline_to_dict


# shared utility tests
def test_kline_to_dict():
    sample_msg = {
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
    result = kline_to_dict(sample_msg)
    assert result["symbol"] == "BTCUSDT"
    assert result["open"] == 50000.0
    assert result["close"] == 50100.0
    assert result["is_closed"] is True
    assert "price_change" in result
    assert "ts" in result


# KafkaProducerService tests
@pytest.fixture
def producer_service():
    return KafkaProducerService(
        bootstrap_servers=["localhost:9092"],
        symbols=["BTCUSDT"],
        interval="1m",
        topic="test_topic",
    )


def test_producer_start(producer_service, mock_kafka_producer):
    with patch("collection_admin.data.kafka_producer.wait_for_kafka") as mock_wait:
        with patch("binance.ThreadedWebsocketManager") as mock_twm:
            mock_twm.return_value.start = MagicMock()
            producer_service.start()
            mock_wait.assert_called_once()
            assert producer_service.producer is not None
            assert producer_service.twm is not None
            producer_service.stop()


def test_producer_stop(producer_service):
    producer_service.producer = MagicMock()
    producer_service.twm = MagicMock()
    producer_service.stop()
    producer_service.twm.stop.assert_called_once()
    producer_service.producer.flush.assert_called_once()
    producer_service.producer.close.assert_called_once()
    assert producer_service._running is False


def test_handle_message(producer_service):
    producer_service._running = True
    producer_service.producer = MagicMock()
    sample_msg = {
        "e": "kline",
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
    producer_service._handle_message(sample_msg)
    producer_service.producer.send.assert_called_once()
    args, _ = producer_service.producer.send.call_args
    assert args[0] == "test_topic"
    assert args[1]["symbol"] == "BTCUSDT"


def test_producer_send_message(producer_service, mock_kafka_producer):
    producer_service._running = True
    producer_service.producer = mock_kafka_producer
    producer_service._handle_message(
        {
            "e": "kline",
            "s": "BTCUSDT",
            "k": {
                "x": True,
                "t": 123,
                "T": 456,
                "o": "50000",
                "c": "50100",
                "h": "50200",
                "l": "49900",
                "v": "1.5",
                "q": "75000",
                "n": 120,
                "V": "0.8",
                "Q": "40000",
            },
        }
    )
    mock_kafka_producer.send.assert_called_once()


# KafkaConsumerService tests
@pytest.fixture
def consumer_service():
    return KafkaConsumerService(
        bootstrap_servers=["localhost:9092"],
        topic="test_topic",
        group_id="test_group",
        mongo_db="test_db",
        mongo_collection="test_coll",
    )


def test_consumer_start(consumer_service, mock_kafka_producer):
    with patch("collection_admin.data.kafka_consumer.wait_for_kafka") as mock_wait:
        consumer_service.start()
        mock_wait.assert_called_once()
        assert consumer_service.consumer is not None
        consumer_service.stop()


def test_consumer_stop(consumer_service):
    consumer_service.consumer = MagicMock()
    consumer_service.stop()
    consumer_service.consumer.close.assert_called_once()
    assert consumer_service._running is False


@patch("collection_admin.data.kafka_consumer.save_to_collection")
def test_consumer_process_message(mock_save, consumer_service):
    class MockMessage:
        value = {"price": 50000}

    consumer_service._process_message(MockMessage())
    mock_save.assert_called_once_with("test_db", "test_coll", {"price": 50000})


# extra tests for edge cases
def test_producer_handle_bad_message(producer_service):
    """Malformed messages should be logged but not crash."""
    producer_service._running = True
    producer_service.producer = MagicMock()

    # invalid message, e.g. missing 'e'
    producer_service._handle_message({"s": "BTCUSDT"})
    producer_service.producer.send.assert_not_called()

    # message with 'k' but 'x' is False, unclosed kline
    producer_service._handle_message({"e": "kline", "s": "BTCUSDT", "k": {"x": False}})
    producer_service.producer.send.assert_not_called()


def test_consumer_failure_handling(consumer_service):
    """If saving to MongoDB fails, consumer should still continue."""
    with patch(
        "collection_admin.data.kafka_consumer.save_to_collection",
        side_effect=Exception("DB error"),
    ):
        msg = MagicMock()
        msg.value = {"price": 50000}
        # no exception should be raised
        consumer_service._process_message(msg)
