import json
import os
import time

import pytest
import requests
from pymongo import MongoClient

# conditional import, skip test if kafka-python is not installed
try:
    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    NoBrokersAvailable = None


@pytest.mark.skipif(not KAFKA_AVAILABLE, reason="kafka-python not installed")
def test_data_flow():
    kafka_endpoint = os.getenv("KAFKA_ENDPOINT", "localhost:9092")
    mongo_endpoint = os.getenv("MONGO_ENDPOINT", "mongodb://localhost:27018")
    fastapi_url = os.getenv("FASTAPI_URL", "http://localhost:8003")

    test_message = {
        "symbol": "TESTUSDT",
        "interval": "1m",
        "open_time": 1620000000000,
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

    # retry creating producer - Kafka may not be ready immediately
    max_retries = 5
    for i in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=kafka_endpoint,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            break
        except NoBrokersAvailable:
            if i == max_retries - 1:
                raise
            time.sleep(2)

    future = producer.send("binance_prices", value=test_message)
    producer.flush()
    result = future.get(timeout=5)
    assert result.topic == "binance_prices"

    # wait for MongoDB to receive message
    mongo_client = MongoClient(mongo_endpoint)
    collection = mongo_client["cryptobot"]["streaming_data_1m"]
    start = time.time()
    doc = None
    while time.time() - start < 30:
        doc = collection.find_one({"symbol": "TESTUSDT"})
        if doc:
            break
        time.sleep(1)
    assert doc is not None, "Test message not found in MongoDB"
    collection.delete_one({"_id": doc["_id"]})

    # verify FastAPI health
    health_response = requests.get(f"{fastapi_url}/api/health", timeout=5)
    assert health_response.status_code == 200
    assert health_response.json().get("status") == "healthy"

    # verify historical endpoint
    historical_response = requests.get(
        f"{fastapi_url}/api/historical/TESTUSDT", timeout=5
    )
    assert historical_response.status_code == 200
