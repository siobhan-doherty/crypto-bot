import json
import socket
import time
import logging
from kafka import KafkaConsumer
from collection_admin.db.mongo_utils import save_to_collection
from collection_admin.config import settings

# config logging for script
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def wait_for_kafka(host, port, timeout=60):
    logger.info(f"Waiting for Kafka at {host}:{port} ...")
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                logger.info("Kafka is ready!")
                return
        except Exception:
            if time.time() - start > timeout:
                logger.error("Timeout waiting for Kafka")
                raise
            time.sleep(2)


wait_for_kafka("kafka", 9092)

consumer = KafkaConsumer(
    "binance_prices",
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    auto_offset_reset="latest",
    group_id="binance-test",
    value_deserializer=lambda x: json.loads(x.decode()),
)

logger.info("Consumer started. Listening...")
for msg in consumer:
    data = msg.value
    logger.info(f"Received: {data}")
    save_to_collection("cryptobot", "streaming_data_1m", data)
    logger.info("Persisted to MongoDB")
