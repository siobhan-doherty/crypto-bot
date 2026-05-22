import sys
import pytest 
from unittest.mock import patch, MagicMock

# add src/ to Python path so collection_admin can get imported
sys.path.insert(0, "src")

# mock kafka module globally to prevent ModuleNotFoundError
sys.modules["kafka"] = MagicMock()
sys.modules["kafka.KafkaConsumer"] = MagicMock()
sys.modules["kafka.KafkaProducer"] = MagicMock()
sys.modules["binance"] = MagicMock()
sys.modules["binance.ThreadedWebsocketManager"] = MagicMock()

@pytest.fixture(autouse = True)
def mock_wait_for_kafka():
    with patch("collection_admin.data.kafka_consumer.wait_for_kafka") as mock1, \
        patch("collection_admin.data.kafka_producer.wait_for_kafka") as mock2:
        yield mock1

@pytest.fixture(scope = "session")
def mock_kafka_producer():
    """Provides a mocked KafkaProducer class"""
    with patch("kafka.KafkaProducer") as mock:
        yield mock

@pytest.fixture(scope = "session")
def mock_mongo_client():
    """Provides a mocked MongoClient"""
    with patch("pymongo.MongoClient") as mock:
        yield mock
