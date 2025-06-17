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
interval = Client.KLINE_INTERVAL_1MINUTE  # 

print("Producer started. Streaming klines every minute...")

while True:
    try:
        now = datetime.utcnow().isoformat()
        for symbol in symbols_to_send:
            klines = client.get_klines(symbol=symbol, interval=interval, limit=1)
            if not klines:
                continue
            last_kline = klines[0]
            # last_kline = [
            #     0 Open time
            #     1 Open
            #     2 High
            #     3 Low
            #     4 Close
            #     5 Volume
            #     6 Close time
            #     7 Quote asset volume
            #     8 Number of trades
            #     9 Taker buy base asset volume
            #    10 Taker buy quote asset volume
            #    11 Ignore
            # ]
            msg = {
                "symbol": symbol,
                "open_time": int(last_kline[0]),
                "open": float(last_kline[1]),
                "high": float(last_kline[2]),
                "low": float(last_kline[3]),
                "close": float(last_kline[4]),
                "volume": float(last_kline[5]),
                "close_time": int(last_kline[6]),
                "quote_volume": float(last_kline[7]),
                "num_trades": int(last_kline[8]),
                "taker_base_volume": float(last_kline[9]),
                "taker_quote_volume": float(last_kline[10]),
                "ts": now
            }
            producer.send('binance_prices', msg)
            print(f"Sent kline: {msg}")
        producer.flush()
        time.sleep(60)  # wait 60 seconds
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
