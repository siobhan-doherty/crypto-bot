import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

# add src/ to Python path so collection_admin may be imported
sys.path.insert(0, "src")

# mock external modules for unit tests
if not os.environ.get("E2E_TEST"):
    sys.modules["kafka"] = MagicMock()
    sys.modules["kafka.KafkaConsumer"] = MagicMock()
    sys.modules["kafka.KafkaProducer"] = MagicMock()
    sys.modules["binance"] = MagicMock()
    sys.modules["binance.ThreadedWebsocketManager"] = MagicMock()


@pytest.fixture(autouse=True)
def mock_wait_for_kafka():
    # only mock if not e2e
    if not os.environ.get("E2E_TEST"):
        with patch("collection_admin.data.kafka_consumer.wait_for_kafka") as mock:
            yield mock
    else:
        yield


@pytest.fixture(scope="session")
def mock_kafka_producer():
    if not os.environ.get("E2E_TEST"):
        with patch("kafka.KafkaProducer") as mock:
            yield mock
    else:
        yield None


@pytest.fixture(scope="session")
def mock_mongo_client():
    if not os.environ.get("E2E_TEST"):
        with patch("pymongo.MongoClient") as mock:
            yield mock
    else:
        yield None


@pytest.fixture(scope="session")
def docker_compose_file():
    """Return path to E2E Docker Compose file."""
    return os.path.join(
        os.path.dirname(__file__), "integration", "docker-compose.e2e.yml"
    )


@pytest.fixture(scope="session")
def docker_services(
    docker_compose_file, docker_compose_project_name, docker_setup, docker_cleanup
):
    # wait for ports
    import socket

    start = time.time()
    while time.time() - start < 60:
        try:
            with socket.create_connection(("localhost", 9092), timeout=2):
                with socket.create_connection(("localhost", 27017), timeout=2):
                    break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError("Timeout waiting for services")
    yield


@pytest.fixture(scope="session")
def kafka_endpoint(docker_services):
    return "localhost:9092"


@pytest.fixture(scope="session")
def mongo_endpoint(docker_services):
    return "mongodb://localhost:27017"
