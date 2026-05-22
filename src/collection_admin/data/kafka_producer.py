import json
import time
import logging
import signal
from typing import List, Optional
from binance import ThreadedWebsocketManager
from kafka import KafkaProducer
from datetime import datetime, timezone
from collection_admin.config import settings
from collection_admin.kafka_utils import wait_for_kafka, kline_to_dict

# config logging for script
logging.basicConfig(
    level = getattr(logging, settings.LOG_LEVEL.upper()),
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class KafkaProducerService:
    def __init__(
        self,
        bootstrap_servers: List[str],
        symbols: List[str],
        interval: str = "1m",
        topic: str = "binance_prices",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.symbols = symbols
        self.interval = interval
        self.topic = topic
        self.producer: Optional[KafkaProducer] = None
        self.twm: Optional[ThreadedWebsocketManager] = None
        self._running = False
    
    def start(self) -> None:
        host, port = self.bootstrap_servers[0].split(":")
        wait_for_kafka(host, int(port))
        self.producer = KafkaProducer(
            bootstrap_servers = self.bootstrap_servers,
            value_serializer = lambda v: json.dumps(v).encode("utf-8"),
        )
        self.twm = ThreadedWebsocketManager(
            api_key = settings.BINANCE_API_KEY,
            api_secret = settings.BINANCE_SECRET_KEY,
        )
        self.twm.start()
        for symbol in self.symbols:
            self.twm.start_kline_socket(
                callback = self._handle_message,
                symbol = symbol, 
                interval = self.interval,
            )
        self._running = True
        logger.info("Kafka producer and WebSocket started")

    def _handle_message(self, msg: dict) -> None:
        if not self._running:
            return
        try:
            if msg.get("e") == "kline" and msg.get("k", {}).get("x", False):
                data = kline_to_dict(msg)
                self.producer.send(self.topic, data)
                logger.debug(f"Sent kline for {data['symbol']}")
        except Exception as e:
            logger.error(f"Error: {e}")
    
    def stop(self) -> None:
        logger.info("Shutting down producer...")
        self._running = False
        if self.twm:
            self.twm.stop()
        if self.producer:
            self.producer.flush()
            self.producer.close()
        logger.info("Producer stopped")

    def run_forever(self) -> None:
        signal.signal(signal.SIGINT, lambda *_: self.stop())
        signal.signal(signal.SIGTERM, lambda *_: self.stop())
        while self._running:
            time.sleep(1)


def main():
    service = KafkaProducerService(
        bootstrap_servers= settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
        symbols = settings.BINANCE_SYMBOLS,
        interval = settings.KAFKA_INTERVAL,
        topic = settings.KAFKA_TOPIC,
    )
    try:
        service.start()
        service.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()


if __name__ == "__main__":
    main()
