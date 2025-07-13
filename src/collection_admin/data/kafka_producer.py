import os
import json
import time
from dotenv import load_dotenv
from binance import ThreadedWebsocketManager
from kafka import KafkaProducer
from datetime import datetime, timezone
from pathlib import Path
import socket
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


# Load .env
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


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

wait_for_kafka('kafka', 9092)

# Kafka producer config
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

symbols_to_send = ['BTCUSDT', 'ETHUSDT']
interval = '1m'  # WebSocket interval format

logging.info("WebSocket Producer started. Streaming real-time klines...")


def get_iso_timestamp():
    """Return current UTC time in ISO 8601 format with milliseconds"""
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def process_kline(msg):
    """Process WebSocket kline message into standardized format """
    k = msg['k']
    return {
        "symbol": msg['s'],
        "open_time": k['t'],
        "open": float(k['o']),
        "high": float(k['h']),
        "low": float(k['l']),
        "close": float(k['c']),
        "volume": float(k['v']),
        "close_time": k['T'],
        "quote_volume": float(k['q']),
        "num_trades": k['n'],
        "taker_base_volume": float(k['V']),
        "taker_quote_volume": float(k['Q']),
        # aditional field calculated from kline data
        "open_datetime": datetime.fromtimestamp(
            k['t']/1000, tz=timezone.utc
        ).isoformat(),
        "close_datetime": datetime.fromtimestamp(
            k['T']/1000, tz=timezone.utc
        ).isoformat(),
        "price_change": float(k['c']) - float(k['o']),
        "price_change_pct": round(
            (float(k['c']) - float(k['o'])) / float(k['o']) * 100, 4
        ),
        "high_low_spread": float(k['h']) - float(k['l']),
        "high_low_spread_pct": round(
            (float(k['h']) - float(k['l'])) / float(k['l']) * 100, 4
        ),
        "ts": get_iso_timestamp(),
        # aditional field for closed kline
        "is_closed": k['x']
    }


def handle_socket_message(msg):
    """Handle incoming WebSocket messages"""
    try:
        if msg['e'] == 'kline' and msg['k']['x']:  # just process closed klines
            processed_msg = process_kline(msg)
            producer.send('binance_prices', processed_msg)
            logging.info(f"Sent kline for {msg['s']} at {processed_msg['ts']}")
    except Exception as e:
        logging.info(f"Error processing message: {e}")


# Start WebSocket
twm = ThreadedWebsocketManager(
    api_key=os.getenv('BINANCE_API_KEY'),
    api_secret=os.getenv('BINANCE_SECRET_KEY')
)
twm.start()


# Subscribe to klines for each symbol
for symbol in symbols_to_send:
    twm.start_kline_socket(
        callback=handle_socket_message,
        symbol=symbol,
        interval=interval
    )


# Keep the connection alive
try:
    while True:
        time.sleep(10)  # keep the main thread alive
except KeyboardInterrupt:
    logging.info("Shutting down...")
    twm.stop()
    producer.flush()
