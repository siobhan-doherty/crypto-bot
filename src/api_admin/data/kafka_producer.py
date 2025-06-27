import os, time, json
from dotenv import load_dotenv
from binance.client import Client
from kafka import KafkaProducer
from datetime import datetime, timezone
from pathlib import Path


# load .env
load_dotenv(dotenv_path = Path(__file__).resolve().parents[2] / ".env")

api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')
client = Client(api_key, secret_key)

# Kafka producer config
producer = KafkaProducer(
    bootstrap_servers = 'kafka:9092',
    value_serializer = lambda v: json.dumps(v).encode('utf-8')
)

symbols_to_send = ['BTCUSDT', 'ETHUSDT']
interval = Client.KLINE_INTERVAL_1MINUTE

print("Producer started. Streaming klines every minute...")

def get_iso_timestamp():
    """Return current UTC time in ISO 8601 format with milliseconds"""
    return datetime.now(timezone.utc).isoformat(timespec = 'milliseconds')

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
        # Additional fields calculated for consistency
        "open_datetime": datetime.fromtimestamp(int(kline_data[0] / 1000), tz=timezone.utc).isoformat(),
        "close_datetime": datetime.fromtimestamp(int(kline_data[6] / 1000), tz=timezone.utc).isoformat(),
        "price_change": float(kline_data[4]) - float(kline_data[1]),
        "price_change_pct": round((float(kline_data[4]) - float(kline_data[1])) / float(kline_data[1]) * 100, 4),
        "high_low_spread": float(kline_data[2]) - float(kline_data[3]),
        "high_low_spread_pct": round((float(kline_data[2]) - float(kline_data[3])) / float(kline_data[3]) * 100, 4),
        "ts": get_iso_timestamp()  # Date ISO 8601 standard
    }

print("Kafka Producer started...")

while True:
    try:
        current_ts = get_iso_timestamp()
        for symbol in symbols_to_send:
            klines = client.get_klines(symbol = symbol, interval = interval, limit = 1)
            if not klines:
                print(f"No klines received for {symbol}")
                continue
            time.sleep(2)  # 2 sec delay per symbol
            msg = process_kline(symbol, klines[0])
            producer.send('binance_prices', msg)
            print(f"Sent kline for {symbol} at {current_ts}")
            
        producer.flush()
        time.sleep(60)  # API rate limit (Binance could ban) and reduce system load

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)  # Wait before retrying to avoid spamming the API
