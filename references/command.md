



# Commands to launch kafka 

## Execute in different terminals
docker exec -it crypto_pyspark python3 src/data/kafka_producer.py
docker exec -it crypto_pyspark python3 src/data/kafka_consume.py


## Check data in MongoDB
docker exec -it crypto_mongo mongosh -u crypto_project -p dst123 --authenticationDatabase admin
db.adminCommand('listDatabases')
use cryptobot
db.getCollectionNames()

db.historical_data.findOne()
db.historical_data.countDocuments()

db.streaming_data.findOne()
db.streaming_data.countDocuments()
db.streaming_data.countDocuments({ "symbol": "BTCUSDT" })
db.streaming_data.countDocuments({ "symbol": "ETHUSDT" })
db.streaming_data.findOne({ "symbol": "BTCUSDT" })
db.streaming_data.findOne({ "symbol": "ETHUSDT" })