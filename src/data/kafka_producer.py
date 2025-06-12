import os
import time
import json
from dotenv import load_dotenv
from binance.client import Client
from kafka import KafkaProducer
from datetime import datetime

# Load .env
load_dotenv()
api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')
client = Client(api_key, secret_key)

# Kafka producer config
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

symbols_to_send = ['BTCUSDT', 'ETHUSDT']

print("Producer started. Streaming prices every 5 seconds...")
while True:
    try:
        # Fetch latest prices
        all_prices = client.get_all_tickers()
        now = datetime.utcnow().isoformat()
        for p in all_prices:
            if p['symbol'] in symbols_to_send:
                # Attach timestamp to each message
                p['ts'] = now
                producer.send('binance_prices', p)
                print(f"Sent: {p}")
        producer.flush()
        time.sleep(5)  # interval between fetches (seconds)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)  # wait before retrying on error