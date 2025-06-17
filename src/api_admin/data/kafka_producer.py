import os
import time
import json
from dotenv import load_dotenv
from binance.client import Client
from kafka import KafkaProducer
from datetime import datetime, timezone

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
interval = Client.KLINE_INTERVAL_1MINUTE

print("Producer started. Streaming klines every minute...")

def get_iso_timestamp():
    """Return current UTC time in ISO 8601 format with milliseconds"""
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

def process_kline(symbol, kline_data):
    """Process raw kline data into standardized format"""
    return {
        "symbol": symbol,
        "open_time": int(kline_data[0]),
        "open": float(kline_data[1]),
        "high": float(kline_data[2]),
        "low": float(kline_data[3]),
        "close": float(kline_data[4]),
        "volume": float(kline_data[5]),
        "close_time": int(kline_data[6]),
        "quote_volume": float(kline_data[7]),
        "num_trades": int(kline_data[8]),  # int (no Long)
        "taker_base_volume": float(kline_data[9]),
        "taker_quote_volume": float(kline_data[10]),
        "ts": get_iso_timestamp(),  # Date ISO 8601 standard
        # Additional fields calculated for consistency
        "price_change": float(kline_data[4]) - float(kline_data[1]),
        "price_change_pct": (float(kline_data[4]) - float(kline_data[1])) / float(kline_data[1]) * 100,
        "high_low_spread": float(kline_data[2]) - float(kline_data[3])
    }

while True:
    try:
        current_ts = get_iso_timestamp()
        for symbol in symbols_to_send:
            klines = client.get_klines(symbol=symbol, interval=interval, limit=1)
            if not klines:
                print(f"No klines received for {symbol}")
                continue
                
            msg = process_kline(symbol, klines[0])
            producer.send('binance_prices', msg)
            print(f"Sent kline for {symbol} at {current_ts}")
            
        producer.flush()
        time.sleep(20)  # wait 60 seconds
        
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)