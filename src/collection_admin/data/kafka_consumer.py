import json
import logging
import signal
from typing import Optional

from kafka import KafkaConsumer

from collection_admin.config import settings
from collection_admin.db.mongo_utils import save_to_collection
from collection_admin.kafka_utils import wait_for_kafka

# config logging for script
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class KafkaConsumerService:
    def __init__(
        self,
        bootstrap_servers: list,
        topic: str,
        group_id: str,
        mongo_db: str = "cryptobot",
        mongo_collection: str = "streaming_data_1m",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.consumer: Optional[KafkaConsumer] = None
        self._running = False

    def start(self) -> None:
        host, port = self.bootstrap_servers[0].split(":")
        wait_for_kafka(host, int(port))
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset="latest",
            group_id=self.group_id,
            value_deserializer=lambda x: json.loads(x.decode()),
        )
        self._running = True
        logger.info(f"Consumer started on topic '{self.topic}'")

    def _process_message(self, msg) -> None:
        data = msg.value
        logger.debug(f"Received: {data}")
        save_to_collection(self.mongo_db, self.mongo_collection, data)
        logger.debug("Persisted to MongoDB")

    def run_forever(self) -> None:
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first")
        signal.signal(signal.SIGINT, lambda *_: self.stop())
        signal.signal(signal.SIGTERM, lambda *_: self.stop())
        while self._running:
            records = self.consumer.poll(timeout_ms=1000)
            for tp, messages in records.items():
                for msg in messages:
                    self._process_message(msg)

    def stop(self) -> None:
        logger.info("Shutting down consumer...")
        self._running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Consumer stopped")


def main():
    service = KafkaConsumerService(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
        topic=settings.KAFKA_TOPIC,
        group_id=settings.KAFKA_CONSUMER_GROUP,
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
