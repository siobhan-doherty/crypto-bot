import json
import time

from kafka import KafkaProducer
from pymongo import MongoClient


def test_data_flow(kafka_endpoint, mongo_endpoint):
    # create a test message, matching schema of streaming_data_1m
    test_message = {
        "symbol": "TESTUSDT",
        "open": 50000.0,
        "high": 50200.0,
        "low": 49900.0,
        "close": 50100.0,
        "volume": 1.5,
        "close_time": 1620000060000,
        "quote_volume": 75000.0,
        "num_trades": 120,
        "taker_base_volume": 0.8,
        "taker_quote_volume": 40000.0,
        "open_datetime": "2021-05-03T00:00:00.000+00:00",
        "close_datetime": "2021-05-03T00:01:00.000+00:00",
        "price_change": 100.0,
        "price_change_pct": 0.2,
        "high_low_spread": 300.0,
        "high_low_spread_pct": 0.6,
        "ts": "2021-05-03T00:01:00.000+00:00",
        "is_closed": True,
    }

    # send message to Kafka
    producer = KafkaProducer(
        bootstrap_servers=kafka_endpoint,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    future = producer.send("binance_prices", value=test_message)
    producer.flush()
    result = future.get(timeout=5)
    assert result.topic == "binance_prices"

    # wait for MongoDB to receive message
    mongo_client = MongoClient(mongo_endpoint)
    collection = mongo_client["cryptobot"]["streaming_data_1m"]
    start_time = time.time()
    doc = None
    while time.time() - start_time < 30:
        doc = collection.find_one({"symbol": "TESTUSDT"})
        if doc:
            break
        time.sleep(1)
    assert doc is not None, "Test message not found in MongoDB within 30 seconds"

    # cleanup, remove test doc
    collection.delete_one({"_id": doc["_id"]})
