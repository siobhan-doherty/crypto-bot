import json
from dotenv import load_dotenv
from kafka import KafkaConsumer
from collection_admin.db.mongo_utils import save_to_collection
import logging
import socket
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


def wait_for_kafka(host, port, timeout=60):
    logging.info(f"Waiting for Kafka at {host}:{port} ...")
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                logging.info("Kafka is ready!")
                return
        except Exception:
            if time.time() - start > timeout:
                logging.info("Timeout waiting for Kafka")
                raise
            time.sleep(2)

load_dotenv(dotenv_path="/app/.env", override=True)
wait_for_kafka('kafka', 9092)

consumer = KafkaConsumer(
    'binance_prices',
    bootstrap_servers='kafka:9092',
    auto_offset_reset='latest',
    group_id='binance-test',
    value_deserializer=lambda x: json.loads(x.decode())
)

logging.info("Consumer started. Listening...")
for msg in consumer:
    data = msg.value
    logging.info(f"Received: {data}")
    save_to_collection("cryptobot", "streaming_data_1m", data)
    logging.info("Persisted to MongoDB")
