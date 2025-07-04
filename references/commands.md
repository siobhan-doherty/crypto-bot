
# clean services
docker ps
docker logs crypto_kafka
docker exec -it crypto_pyspark ping kafka
docker exec -it crypto_pyspark telnet kafka 9092

# clean volumns
docker-compose down -v
# clean containers
docker-compose down --remove-orphans 

 # Commands to launch data architecture
docker-compose build
docker-compose build --no-cache
docker-compose up -d


# Commands to launch kafka-streaming

## Execute in different terminals
docker exec -it crypto_pyspark python3 src/collection_admin/data/initialize_historical_data.py
docker exec -it crypto_pyspark python3 src/collection_admin/data/kafka_producer.py
docker exec -it crypto_pyspark python3 src/collection_admin/data/kafka_consumer.py

# launch dash
docker exec -it crypto_dash python3 /app/src/api_user/visualization/dash_app.py


docker volume inspect apr25_bde_int_opa_team_a_mongo_data

## Check data in MongoDB
docker exec -it crypto_mongo mongosh -u <USER_NAME> -p <PASSWORD> --authenticationDatabase admin

db.adminCommand('listDatabases')
use cryptobot
db.getCollectionNames()

db.historical_data_15m.findOne()
db.historical_data_15m.countDocuments()
db.historical_data_15m.findOne({ "symbol": "BTCUSDT" })
db.historical_data_15m.findOne({ "symbol": "ETHUSDT" })

db.streaming_data.findOne()
db.streaming_data.countDocuments()
db.streaming_data.countDocuments({ "symbol": "BTCUSDT" })
db.streaming_data.countDocuments({ "symbol": "ETHUSDT" })
db.streaming_data.findOne({ "symbol": "BTCUSDT" })
db.streaming_data.findOne({ "symbol": "ETHUSDT" })

db.streaming_data.drop()

docker-compose down -v
docker-compose up --build --force-recreate
