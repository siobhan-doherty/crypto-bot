from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'binance_prices',
    bootstrap_servers='kafka:9092',
    auto_offset_reset='earliest',
    group_id='binance-test',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for message in consumer:
    print(message.value)
    break  # Remove or adjust for continuous reading
