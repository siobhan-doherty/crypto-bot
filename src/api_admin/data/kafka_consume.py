from kafka import KafkaConsumer
import json
from pymongo import MongoClient

# Kafka consumer config
consumer = KafkaConsumer(
    'binance_prices',
    bootstrap_servers='kafka:9092',
    auto_offset_reset='latest',
    group_id='binance-test',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# MongoDB 
mongo_client = MongoClient('mongodb://crypto_project:dst123@crypto_mongo:27017/')
db = mongo_client['cryptobot']
collection = db['streaming_data']

print("Consumer started. Listening for messages...")
for message in consumer:
    data = message.value
    print("Received:", data)
    # save in MongoDB
    collection.insert_one(data)
    print("Saved to MongoDB:", data['symbol'], data['ts'])
