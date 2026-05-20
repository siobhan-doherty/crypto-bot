import json
import time
import socket
import logging
from binance import ThreadedWebsocketManager
from kafka import KafkaProducer
from datetime import datetime, timezone
from collection_admin.config import settings

# config logging for script
logging.basicConfig(
    level = getattr(logging, settings.LOG_LEVEL.upper()),
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def wait_for_kafka(host, port, timeout = 60):
    logging.info(f"Waiting for Kafka at {host}:{port} ...")
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout = 2):
                logger.info("Kafka is ready!")
                return
        except Exception:
            if time.time() - start > timeout:
                logger.info("Timeout waiting for Kafka")
                raise
            time.sleep(2)

wait_for_kafka('kafka', 9092)

producer = KafkaProducer(
    bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer = lambda v: json.dumps(v).encode('utf-8')
)

symbols_to_send = ['BTCUSDT', 'ETHUSDT']
interval = '1m'  # WebSocket interval format

logger.info("WebSocket Producer started. Streaming real-time klines...")


def get_iso_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec = 'milliseconds')


def process_kline(msg):
    k = msg["k"]
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
        "open_datetime": datetime.fromtimestamp(
            k['t']/1000, tz = timezone.utc
        ).isoformat(),
        "close_datetime": datetime.fromtimestamp(
            k['T']/1000, tz = timezone.utc
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
        "is_closed": k['x']
    }


def handle_socket_message(msg):
    try:
        if msg['e'] == 'kline' and msg['k']['x']:
            processed_msg = process_kline(msg)
            producer.send("binance_prices", processed_msg)
            logger.info(f"Sent kline for {msg['s']} at {processed_msg['ts']}")
    except Exception as e:
        logger.info(f"Error processing message: {e}")


# Start WebSocket
twm = ThreadedWebsocketManager(
    api_key = settings.BINANCE_API_KEY,
    api_secret = settings.BINANCE_SECRET_KEY
)
twm.start()


# Subscribe to klines for each symbol
for symbol in symbols_to_send:
    twm.start_kline_socket(
        callback = handle_socket_message,
        symbol = symbol,
        interval = interval
    )


# Keep the connection alive
try:
    while True:
        time.sleep(10)  # keep the main thread alive
except KeyboardInterrupt:
    logger.info("Shutting down...")
    twm.stop()
    producer.flush()
