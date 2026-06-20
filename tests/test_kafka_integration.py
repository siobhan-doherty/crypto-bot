import json
import os
import time

import pytest
from kafka import KafkaConsumer, KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from testcontainers.kafka import KafkaContainer

# disable global Kafka mocks from conftest.py
os.environ["E2E_TEST"] = "1"

@pytest.fixture(scope="module")
def kafka_container():
    with KafkaContainer("confluentinc/cp-kafka:7.4.0") as kafka:
        # wait few seconds for Kafka to fully start
        time.sleep(5)
        yield kafka


def test_kafka_producer_consumer_integration(kafka_container):
    bootstrap_servers = kafka_container.get_bootstrap_server()
    topic = "test_topic"
    group_id = "test_group"

    # create topic explicitly
    admin_client = KafkaAdminClient(
        bootstrap_servers = bootstrap_servers
    )
    admin_client.create_topics([
        NewTopic(
            name = topic, 
            num_partitions = 1, 
            replication_factor = 1
        )
    ])

    # producer sends message
    producer = KafkaProducer(
        bootstrap_servers = bootstrap_servers,
        value_serializer = lambda v: json.dumps(v).encode("utf-8")
    )
    test_message = {"price": 100}
    future = producer.send(topic, test_message)
    producer.flush()
    future.get(timeout = 10)  # wait for acknowledgment
    producer.close()

    # consumer reads message
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers = bootstrap_servers,
        auto_offset_reset = "earliest",
        enable_auto_commit = True,
        group_id = group_id,
        value_deserializer = lambda m: json.loads(m.decode("utf-8"))
    )

    # poll until we get message, max 10 secs
    received = None
    start = time.time()
    while time.time() - start < 10:
        records = consumer.poll(timeout_ms = 1000)
        for tp, messages in records.items():
            for msg in messages:
                received = msg.value
                break
            if received:
                break
        if received:
            break

    consumer.close()
    assert received == test_message
