from dotenv import load_dotenv
import os
from binance.client import Client
from kafka import KafkaProducer
import json

# Load .env
load_dotenv()

# Connect to Binance
api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')
client = Client(api_key, secret_key)

# Fetch all prices
all_prices = client.get_all_tickers()

# Filter for BTC/USDT and ETH/USDT only
symbols_to_send = ['BTCUSDT', 'ETHUSDT']
filtered_prices = [p for p in all_prices if p['symbol'] in symbols_to_send]

# Set up Kafka producer
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',  # or your Kafka host
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send filtered data
producer.send('binance_prices', filtered_prices)
producer.flush()
print("Data sent to Kafka topic 'binance_prices':", filtered_prices)