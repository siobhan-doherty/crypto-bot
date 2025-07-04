import os, json
from dotenv import load_dotenv
from kafka import KafkaConsumer
from collection_admin.db.mongo_utils import save_to_collection
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


load_dotenv(dotenv_path="/app/.env", override=True)

consumer = KafkaConsumer(
    'binance_prices',
    bootstrap_servers = 'kafka:9092',
    auto_offset_reset = 'latest',
    group_id = 'binance-test',
    value_deserializer = lambda x: json.loads(x.decode())
)

logging.info("Consumer started. Listening...")
for msg in consumer:
    data = msg.value
    logging.info(f"Received: {data}")
    save_to_collection("cryptobot", "streaming_data_1m", data)
    logging.info("Persisted to MongoDB")
