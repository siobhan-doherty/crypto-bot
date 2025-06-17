
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
docker exec -it crypto_pyspark python3 src/data/kafka_producer.py
docker exec -it crypto_pyspark python3 src/data/kafka_consume.py


## Check data in MongoDB
docker exec -it crypto_mongo mongosh -u crypto_project -p dst123 --authenticationDatabase admin

db.adminCommand('listDatabases')
use cryptobot
db.getCollectionNames()

db.historical_data.findOne()
db.historical_data.countDocuments()
db.historical_data.findOne({ "symbol": "BTCUSDT" })
db.historical_data.findOne({ "symbol": "ETHUSDT" })

db.streaming_data.findOne()
db.streaming_data.countDocuments()
db.streaming_data.countDocuments({ "symbol": "BTCUSDT" })
db.streaming_data.countDocuments({ "symbol": "ETHUSDT" })
db.streaming_data.findOne({ "symbol": "BTCUSDT" })
db.streaming_data.findOne({ "symbol": "ETHUSDT" })


db.streaming_data.drop()


docker-compose down -v
docker-compose up --build --force-recreate
docker exec -it crypto_pyspark python3 src/data/kafka_producer.py


apr25_bde_int_opa_team_a/
├── docker-compose.yml
├── requirements.txt
├── .env
├── README.md
├── LICENSE

├── notebooks/
│   ├── Check Mongodb.ipynb
│   ├── Kafka.ipynb
│   └── ...

├── src/
│   ├── api_admin/
│   │   ├── docker/
│   │   │   └── Dockerfile.jupyter   ← para Spark + Jupyter
│   │   ├── data/
│   │   │   ├── kafka_producer.py
│   │   │   ├── kafka_consume.py
│   │   │   ├── collect_historical_data.py
│   │   │   └── ...
│   │   ├── db/
│   │   │   └── mongo_utils.py
│   │   └── __init__.py

│   ├── api_user/
│   │   ├── docker/
│   │   │   ├── Dockerfile.dash
│   │   │   └── Dockerfile.data_collector
│   │   ├── visualization/
│   │   │   └── dash_app.py
│   │   └── __init__.py

├── references/
│   └── ...
